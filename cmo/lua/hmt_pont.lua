-- hmt_pont.lua : l'actuateur du pont HMT dans Command: Modern Operations ( voir cmo/LISEZMOI.md ).
--
-- Chargé par l'action de l'événement HMT_PONT ( déclencheur RegularTime, 1 s de jeu ) chaque fois que HMT_tic
-- n'existe pas : les globales Lua ne survivent pas au rechargement d'un scénario.
--
-- ALLER     : le moteur écrit Lua/hmt_pont/cmd_<n>.lua = HMT_commande( n, nonce, function( R ) ... end ).
-- RETOUR    : un reçu par commande, ImportExport/hmt_r_<n>.inst, écrit par ScenEdit_ExportInst ( champ Comments ) :
--             les lignes « R CLE nombres », puis « ECHO n nonce k code detail coeur », puis « FIN ».
-- BATTEMENT : ImportExport/hmt_sync.inst à chaque passage : « SYNC n coeur version lecteur build », puis « FIN ».
--             Le coeur ordonne reçus et battements : ce sont deux fichiers, sans ordre commun de lecture.
--
-- QUE DES NOMBRES : HMT_R refuse tout ce qui n'est pas un nombre fini. Seule la ligne ERR d'une commande en échec
-- porte du texte ; cmo_labo.py la met dans l'exception, pour un humain, jamais dans un résultat.
--
-- Codes du reçu : 0 exécutée, 1 erreur Lua pendant l'exécution, 2 le fichier ne compile pas, 3 refus ( detail =
-- code de REFUS_LUA dans cmo_labo.py ).

HMT_VERSION = 5
HMT_CAMPS = { 'Stratis', 'Malden' }                          -- = CAMPS de cmo_labo.py, dans le même ordre
HMT_GENRES = { 'Air', 'Ship', 'Submarine', 'Facility' }      -- = GENRES de cmo_labo.py
HMT_n = HMT_n or 0                                           -- dernière commande prise
HMT_coeur = HMT_coeur or 0                                   -- battements depuis le chargement
HMT_attendu = HMT_attendu or 0                               -- commande en cours de lecture
HMT_calme = HMT_calme or 0                                   -- passages de suite sans commande
-- Chaque RunScript sur un fichier absent écrit une erreur dans Logs/LuaHistory ( pas de mode silencieux, pas de io ni de
-- os.rename pour tester l'existence : sonde du 29/09 ). Après HMT_CALME passages sans commande, on ne cherche plus qu'un
-- passage sur HMT_PAS_CALME : dix fois moins de lignes ; la première commande après un silence attend 10 s au plus.
HMT_CALME, HMT_PAS_CALME = 30, 10

local function propre(s)
    s = string.gsub(tostring(s), '[\r\n]+', ' ')
    return string.sub(s, 1, 300)
end

local function ecrire(nom, texte)
    local camps = VP_GetSides()
    if camps == nil or #camps == 0 then error('aucun camp dans le scénario : lancer hmt_pont/installer.lua') end
    ScenEdit_ExportInst(camps[1].name, {}, { filename = nom, name = 'HMT', comment = texte })
end

local function nombre(v)
    local x = tonumber(v)
    if x == nil or x ~= x or x == math.huge or x == -math.huge then
        error('HMT_R : valeur non numérique ' .. propre(v))
    end
    if math.type(x) == 'integer' then return tostring(x) end
    if x == math.floor(x) and math.abs(x) < 1e15 then return string.format('%d', x) end
    return string.format('%.10g', x)
end

-- 1 = loadfile ( relit le fichier à chaque fois, distingue « absent » de « ne compile pas » ),
-- 2 = ScenEdit_RunScript ( si le bac à sable de CMO retire loadfile ).
function HMT_lecteur()
    if loadfile ~= nil and HMT_BASE ~= nil then return 1 end
    return 2
end

function HMT_commande(n, nonce, corps)
    local lignes = {}
    local function R(cle, valeurs)
        if type(cle) ~= 'string' or not string.match(cle, '^[A-Z_]+$') then error('HMT_R : clé invalide') end
        local t = { 'R', cle }
        for i = 1, #(valeurs or {}) do t[#t + 1] = nombre(valeurs[i]) end
        lignes[#lignes + 1] = table.concat(t, ' ')
    end
    local ok, err = pcall(corps, R)
    local code, detail = 0, 0
    if not ok then
        lignes = {}
        local r = string.match(tostring(err), 'HMT_REFUS (%d+)')
        if r then code, detail = 3, tonumber(r) else code = 1 end
    end
    HMT_n = n
    local fin = string.format('ECHO %d %d %d %d %d %d', n, nonce, #lignes, code, detail, HMT_coeur)
    if code == 1 then fin = fin .. '\nERR ' .. propre(err) end
    lignes[#lignes + 1] = fin
    lignes[#lignes + 1] = 'FIN'
    ecrire('hmt_r_' .. n .. '.inst', table.concat(lignes, '\n'))
end

-- Prend la commande n si elle est là. Rend false quand il n'y a rien à prendre.
local function prendre(n)
    local rel = 'hmt_pont/cmd_' .. n .. '.lua'
    HMT_attendu = n
    if HMT_lecteur() == 1 then
        local f, err = loadfile(HMT_BASE .. 'Lua/' .. rel)
        if f == nil then
            if string.find(tostring(err), 'cannot open', 1, true) then return false end
            -- Présent mais ne compile pas : on le dit et on passe au suivant, sinon le pont reste bloqué sur n.
            HMT_n = n
            ecrire('hmt_r_' .. n .. '.inst', string.format('ECHO %d 0 0 2 0 %d\nERR %s\nFIN', n, HMT_coeur, propre(err)))
            return true
        end
        f()
        return true
    end
    -- RunScript ne distingue pas « absent » de « ne compile pas » ( cmo_labo compile avant d'écrire ), et peut lever au
    -- lieu de rendre nil : la seule preuve qu'une commande a été prise est que HMT_commande a avancé HMT_n.
    pcall(ScenEdit_RunScript, rel)
    return HMT_n >= n
end

-- GetBuildNumber() rend « v1.10 - Build 1900.20 » en 1.10 : on garde les nombres, joints par des points.
function HMT_build()
    local b = {}
    for x in string.gmatch(tostring(GetBuildNumber()), '%d+') do b[#b + 1] = x end
    return table.concat(b, '.')
end

function HMT_battre()
    local build = HMT_build()
    ecrire('hmt_sync.inst', string.format('SYNC %d %d %d %d %s\nFIN', HMT_n, HMT_coeur, HMT_VERSION, HMT_lecteur(), build))
end

-- L'action de l'événement HMT_PONT. Ne lève jamais : une erreur dans une action d'événement arrêterait le pont.
-- UNE commande par passage : CMO applique certains effets entre deux passages ( une suppression, sonde du 29/09 ) ;
-- ainsi chaque commande voit le monde que la précédente a laissé.
function HMT_tic()
    HMT_coeur = HMT_coeur + 1
    if HMT_calme >= HMT_CALME and HMT_coeur % HMT_PAS_CALME ~= 0 then
        pcall(HMT_battre)
        return
    end
    local avant = HMT_n
    local ok, err = pcall(prendre, HMT_n + 1)
    if HMT_n > avant then HMT_calme = 0 else HMT_calme = HMT_calme + 1 end
    if not ok then
        -- La commande attendue a planté hors de son pcall ( ExportInst ?) : on la passe, le moteur verra SansRecu.
        if HMT_attendu > HMT_n then HMT_n = HMT_attendu end
        pcall(ecrire, 'hmt_panne.inst', 'PANNE ' .. propre(err) .. '\nFIN')
    end
    pcall(HMT_battre)                   -- APRÈS la commande : un battement de coeur c dit où en est n après ce passage
end

-- --- LE REGISTRE : numéro de front -> unité. Le nom « HMT-<numéro> » est la mémoire qui survit au rechargement.
function HMT_recenser()
    HMT_unites = {}
    for ci, nom in ipairs(HMT_CAMPS) do
        local ok, camp = pcall(VP_GetSide, { side = nom })
        if ok and camp ~= nil then
            for _, u in ipairs(camp.units or {}) do
                local k = string.match(u.name or '', '^HMT%-(%d+)$')
                if k then HMT_unites[tonumber(k)] = { guid = u.guid, camp = ci } end
            end
        end
    end
    return HMT_unites
end

local function registre()
    if HMT_unites == nil then HMT_recenser() end
    return HMT_unites
end

local function unite(guid)
    local ok, u = pcall(ScenEdit_GetUnit, { guid = guid })
    if ok then return u end
    return nil
end

-- --- LES OUTILS : appelés par les commandes, avec des nombres seulement.
function HMT_canari(R)
    R('CANARI', { HMT_n, HMT_VERSION, #HMT_CAMPS, HMT_lecteur() })
    local b = {}
    for x in string.gmatch(tostring(GetBuildNumber()), '%d+') do b[#b + 1] = tonumber(x) end
    R('BUILD', b)
    R('TEMPS', { ScenEdit_CurrentTime() })
end

function HMT_etat(R)
    local vivants = {}
    for i = 1, #HMT_CAMPS do vivants[i] = 0 end
    for _, e in pairs(registre()) do
        if unite(e.guid) ~= nil then vivants[e.camp] = vivants[e.camp] + 1 end
    end
    for i, nom in ipairs(HMT_CAMPS) do
        local ok, camp = pcall(VP_GetSide, { side = nom })
        local total = -1
        if ok and camp ~= nil and camp.units ~= nil then total = #camp.units end
        R('CAMP', { i, vivants[i], total })
    end
end

function HMT_poser(R, camp, genre, dbid, numero, lat, lon, alt, loadout)
    local reg = registre()
    if HMT_CAMPS[camp] == nil then error('HMT_REFUS 1') end
    if HMT_GENRES[genre] == nil then error('HMT_REFUS 2') end
    if reg[numero] ~= nil and unite(reg[numero].guid) ~= nil then error('HMT_REFUS 3') end
    local t = { side = HMT_CAMPS[camp], type = HMT_GENRES[genre], unitname = 'HMT-' .. numero, dbid = dbid,
                latitude = lat, longitude = lon }
    if genre == 1 then
        t.altitude = alt
        if loadout > 0 then t.loadoutid = loadout end
    end
    local u = ScenEdit_AddUnit(t)
    if u == nil then error('HMT_REFUS 4') end
    reg[numero] = { guid = u.guid, camp = camp }
    R('POSE', { numero, camp, u.latitude, u.longitude })
end

-- Deux camps en guerre : chacun voit l'autre hostile ( la posture se règle dans les deux sens ). Rend 1 par sens
-- relu hostile dans CMO.
function HMT_hostiles(R, a, b)
    if HMT_CAMPS[a] == nil or HMT_CAMPS[b] == nil or a == b then error('HMT_REFUS 1') end
    ScenEdit_SetSidePosture(HMT_CAMPS[a], HMT_CAMPS[b], 'H')
    ScenEdit_SetSidePosture(HMT_CAMPS[b], HMT_CAMPS[a], 'H')
    local ab = ScenEdit_GetSidePosture(HMT_CAMPS[a], HMT_CAMPS[b]) == 'H'
    local ba = ScenEdit_GetSidePosture(HMT_CAMPS[b], HMT_CAMPS[a]) == 'H'
    R('HOSTILES', { a, b, ab and 1 or 0, ba and 1 or 0 })
end

function HMT_aller(R, numero, lat, lon)
    local e = registre()[numero]
    if e == nil or unite(e.guid) == nil then error('HMT_REFUS 5') end
    ScenEdit_SetUnit({ guid = e.guid,
                       course = { { latitude = lat, longitude = lon, TypeOf = 'ManualPlottedCourseWaypoint' } } })
    R('ORDRE', { numero, lat, lon })
end

-- LES LOTS : tous les ordres d'un tour en un seul envoi ( règle de Younes pour Arma ). Chaque élément est tenté à part :
-- un refus ne fait pas tomber le lot, et le reçu dit ce qui a été fait ( POSE / ORDRE ) et ce qui ne l'a pas été
-- ( REFUSE numéro code : code 0 = erreur Lua qui n'est pas un refus ; ABSENT numéro ).
function HMT_poser_lot(R, camp, genre, dbid, alt, loadout, ...)
    local t = { ... }
    if #t % 3 ~= 0 then error('HMT_poser_lot : numéro, lat, lon par avion') end
    for i = 1, #t, 3 do
        local ok, err = pcall(HMT_poser, R, camp, genre, dbid, t[i], t[i + 1], t[i + 2], alt, loadout)
        if not ok then R('REFUSE', { t[i], tonumber(string.match(tostring(err), 'HMT_REFUS (%d+)')) or 0 }) end
    end
end

function HMT_aller_tous(R, lat, lon, ...)
    for _, k in ipairs({ ... }) do
        local e = registre()[k]
        if e == nil or unite(e.guid) == nil then
            R('ABSENT', { k })
        else
            ScenEdit_SetUnit({ guid = e.guid,
                               course = { { latitude = lat, longitude = lon, TypeOf = 'ManualPlottedCourseWaypoint' } } })
            R('ORDRE', { k, lat, lon })
        end
    end
end

-- LES MISSIONS : une patrouille de défense aérienne ( Patrol AAW ) par identifiant, nommée HMT-P<id>, sur une zone de 4
-- points de référence en carré autour d'un centre. Créée au premier appel ; ensuite ses points bougent, la mission reste
-- ( et ses avions aussi ). C'est l'IA de CMO qui vole, engage, se ravitaille et rentre : on ne pilote pas l'avion.
function HMT_patrouille(R, id, camp, lat, lon, demi_km)
    local cote = HMT_CAMPS[camp]
    if cote == nil then error('HMT_REFUS 1') end
    local nom = 'HMT-P' .. id
    local dlat = demi_km / 111.32
    local dlon = demi_km / (111.32 * math.cos(math.rad(lat)))
    local coins = { { lat + dlat, lon - dlon }, { lat + dlat, lon + dlon }, { lat - dlat, lon + dlon }, { lat - dlat, lon - dlon } }
    local ok, m = pcall(ScenEdit_GetMission, cote, nom)
    local existe = ok and m ~= nil
    local noms = {}
    for i, c in ipairs(coins) do
        noms[i] = nom .. '-' .. i
        if existe then
            ScenEdit_SetReferencePoint({ side = cote, name = noms[i], latitude = c[1], longitude = c[2] })
        else
            ScenEdit_AddReferencePoint({ side = cote, name = noms[i], latitude = c[1], longitude = c[2] })
        end
    end
    if not existe and ScenEdit_AddMission(cote, nom, 'Patrol', { type = 'AAW', zone = noms }) == nil then
        error('HMT_REFUS 6')
    end
    R('PATROUILLE', { id, camp, existe and 0 or 1 })
end

function HMT_affecter(R, id, ...)
    local nom = 'HMT-P' .. id
    for _, k in ipairs({ ... }) do
        local e = registre()[k]
        if e == nil or unite(e.guid) == nil then
            R('ABSENT', { k })
        else
            local ok, r = pcall(ScenEdit_AssignUnitToMission, e.guid, nom)
            if ok and r ~= false then R('AFFECTE', { k, id }) else R('REFUSE', { k, 6 }) end
        end
    end
end

-- Les vivants ( U camp numéro lat lon alt ) et les morts depuis le dernier relevé ( MORT camp numéro ).
function HMT_positions(R)
    local reg = registre()
    local numeros = {}
    for k in pairs(reg) do numeros[#numeros + 1] = k end
    table.sort(numeros)
    for _, k in ipairs(numeros) do
        local e = reg[k]
        local u = unite(e.guid)
        if u == nil then
            R('MORT', { e.camp, k })
            reg[k] = nil
        else
            R('U', { e.camp, k, u.latitude, u.longitude, u.altitude or 0 })
        end
    end
end

-- Table rase des unités HMT. CMO 1.10 retire une unité supprimée au passage SUIVANT ( sonde du 29/09 : DeleteUnit rend
-- vrai, mais GetUnit et la liste du camp la montrent encore dans le même passage ). La preuve est donc HMT_recompter,
-- une autre commande, donc un autre passage.
function HMT_nettoyer(R)
    local avant, acceptees = 0, 0
    for _, e in pairs(HMT_recenser()) do
        avant = avant + 1
        local ok, r = pcall(ScenEdit_DeleteUnit, { guid = e.guid }, true)
        if ok and r == true then acceptees = acceptees + 1 end
    end
    HMT_unites = nil
    R('NETTOYE', { avant, acceptees })
end

function HMT_recompter(R)
    local m = 0
    for _ in pairs(HMT_recenser()) do m = m + 1 end
    R('RESTANTES', { m })
end
