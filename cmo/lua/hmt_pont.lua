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

HMT_VERSION = 8
-- Les camps : ceux de hmt_config.lua ( écrit par deployer.py depuis le théâtre ), sinon la guerre des îles. Même ordre que
-- Labo( camps = ... ) ; le canari rend leur signature, calculée des deux côtés.
HMT_CAMPS = HMT_CAMPS_CONFIG or { 'Stratis', 'Malden' }
HMT_GENRES = { 'Air', 'Ship', 'Submarine', 'Facility', 'Vehicle' }   -- = GENRES de cmo_labo.py ; Vehicle : un véhicule
-- seul de DataGroundUnit ( T-72B3 ), les formations au sol étant des Facility mobiles ( sonde du 02/10 )
-- Les vraies installations livrées avec CMO ( ImportExport/<pays>/*.inst ), écrites par deployer.py depuis le théâtre :
-- le moteur n'envoie qu'un INDEX dans cette liste, jamais un nom de fichier.
HMT_INSTALLATIONS = HMT_INSTALLATIONS_CONFIG or {}
-- Les réglages de doctrine que le moteur peut toucher ( index = DOCTRINE de cmo_labo.py ) ; valeurs relues dans CMO.
HMT_DOCTRINE = { 'quick_turnaround_for_aircraft', 'air_operations_tempo', 'bingo_threshold', 'fuel_state_rtb',
                 'weapon_state_rtb', 'weapon_control_status_air', 'weapon_control_status_surface',
                 'weapon_control_status_subsurface', 'weapon_control_status_land', 'engage_opportunity_targets',
                 'use_nuclear_weapons', 'withdraw_on_damage', 'withdraw_on_fuel' }
-- Types des lignes de pertes et dépenses de CMO, en nombre ( = TYPES_BILAN de cmo_labo.py ).
HMT_TYPES = { Aircraft = 1, Ship = 2, Submarine = 3, Facility = 4, Weapon = 5, Vehicle = 6, Satellite = 7 }
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
-- La signature des noms de camps : somme des octets pondérés par leur place, modulo 1 000 000 007 ( = signature_camps
-- de cmo_labo.py ). Aucun nom ne remonte : un nombre suffit à savoir si les deux côtés parlent des mêmes camps.
function HMT_signature_liste(liste)
    local s = 0
    for i, nom in ipairs(liste) do
        for j = 1, #nom do s = (s + string.byte(nom, j) * (i * 31 + j)) % 1000000007 end
    end
    return s
end

function HMT_signature_camps() return HMT_signature_liste(HMT_CAMPS) end

function HMT_canari(R)
    R('CANARI', { HMT_n, HMT_VERSION, #HMT_CAMPS, HMT_lecteur() })
    R('CAMPS_SIG', { HMT_signature_camps() })
    R('INST_SIG', { #HMT_INSTALLATIONS, HMT_signature_liste(HMT_INSTALLATIONS) })
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

-- Des avions posés SUR une base ( une installation HMT déjà posée, du même camp ) : une mission les fait décoller, ils y
-- reviennent se ravitailler. Nés en vol sans base, ils tombaient à sec ( guerre du 29/09 : 37 des 48 pertes de Malden ).
function HMT_poser_base_lot(R, camp, dbid, loadout, base, ...)
    -- Un lot n'échoue jamais à moitié : une base invalide refuse SES avions un par un ( REFUSE 7 ou 8 ), sans lever ; lever
    -- ici effacerait le reçu des lots déjà posés dans la même commande, qui existeraient pourtant dans CMO.
    local cote = HMT_CAMPS[camp]
    local reg = registre()
    local b = reg[base]
    local defaut = nil
    if cote == nil then defaut = 1
    elseif b == nil or unite(b.guid) == nil then defaut = 7
    elseif b.camp ~= camp then defaut = 8 end
    for _, k in ipairs({ ... }) do
        if defaut then
            R('REFUSE', { k, defaut })
        elseif reg[k] ~= nil and unite(reg[k].guid) ~= nil then
            R('REFUSE', { k, 3 })
        else
            local t = { side = cote, type = 'Air', unitname = 'HMT-' .. k, dbid = dbid, base = b.guid }
            if loadout > 0 then t.loadoutid = loadout end
            local ok, u = pcall(ScenEdit_AddUnit, t)
            if ok and u ~= nil then
                reg[k] = { guid = u.guid, camp = camp }
                R('POSE', { k, camp, u.latitude or 0, u.longitude or 0 })
            else
                R('REFUSE', { k, 4 })
            end
        end
    end
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

-- Le journal des messages de CMO ( tirs, détections, pertes et leur cause ) écrit dans Logs/hmt_messages_<id>.txt.
-- Le nom est composé ICI, d'un nombre : aucun texte du moteur n'entre dans CMO.
function HMT_journal(R, id)
    SetScenarioMessageLogPath('hmt_messages_' .. string.format('%d', id) .. '.txt')
    R('JOURNAL', { id })
end

-- LES MISSIONS : une patrouille de défense aérienne ( Patrol AAW ) par identifiant, nommée HMT-P<id>, sur une zone de 4
-- points de référence en carré autour d'un centre. Créée au premier appel ; ensuite ses points bougent, la mission reste
-- ( et ses avions aussi ). C'est l'IA de CMO qui vole, engage, se ravitaille et rentre : on ne pilote pas l'avion.
-- tiers : 1 = règle du tiers de CMO ( un tiers en vol, pour durer ), 0 = tout le paquet part ; nil = réglage de CMO.
function HMT_patrouille(R, id, camp, lat, lon, demi_km, tiers)
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
    if tiers ~= nil then pcall(ScenEdit_SetMission, cote, nom, { OneThirdRule = (tiers == 1) }) end
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

-- Les vivants ( U camp numéro lat lon alt ) et les morts depuis le dernier relevé ( MORT camp numéro ), pour les
-- numéros de [ min, max ] ( tous sans bornes ). Les milliers d'éléments fixes des vraies bases restent hors du relevé :
-- leurs morts viennent du journal de CMO, leurs dégâts de HMT_etats ( 29/09 : sonder des milliers d'installations
-- avait ralenti CMO à x0,13 ).
function HMT_positions(R, min, max)
    local reg = registre()
    local numeros = {}
    for k in pairs(reg) do
        if (min == nil or k >= min) and (max == nil or k <= max) then numeros[#numeros + 1] = k end
    end
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
    -- Les éléments d'abord, les groupes ( une vraie base importée ) ensuite : supprimer un groupe peut emporter ses
    -- éléments, dont la suppression échouerait alors. Un groupe déjà parti n'est pas une faute ; HMT_recompter prouve.
    -- Les ORPHELINS aussi : une unité de nos camps qui n'est pas HMT vient d'un import interrompu avant l'adoption
    -- ( 02/10 : 111 éléments de 4 bases construites, invisibles à la table rase, restés dans le scénario ). Nos camps ne
    -- contiennent que des unités HMT ; les fantômes ( rafales de canon, que GetUnit ne rend pas ) restent.
    local avant, acceptees, groupes = 0, 0, {}
    local cibles = {}
    for _, e in pairs(HMT_recenser()) do cibles[#cibles + 1] = e.guid end
    for _, nom in ipairs(HMT_CAMPS) do
        local ok, s = pcall(VP_GetSide, { side = nom })
        for _, x in ipairs((ok and s and s.units) or {}) do
            if not string.match(x.name or '', '^HMT%-%d+$') and unite(x.guid) ~= nil then cibles[#cibles + 1] = x.guid end
        end
    end
    for _, g in ipairs(cibles) do
        avant = avant + 1
        local u = unite(g)
        if u ~= nil and u.type == 'Group' then
            groupes[#groupes + 1] = g
        else
            local ok, r = pcall(ScenEdit_DeleteUnit, { guid = g }, true)
            if ok and r == true then acceptees = acceptees + 1 end
        end
    end
    for _, g in ipairs(groupes) do
        pcall(ScenEdit_DeleteUnit, { guid = g }, true)
        acceptees = acceptees + 1
    end
    HMT_unites = nil
    R('NETTOYE', { avant, acceptees })
end

function HMT_recompter(R)
    local m = 0
    for _ in pairs(HMT_recenser()) do m = m + 1 end
    for _, nom in ipairs(HMT_CAMPS) do
        local ok, s = pcall(VP_GetSide, { side = nom })
        for _, x in ipairs((ok and s and s.units) or {}) do
            if not string.match(x.name or '', '^HMT%-%d+$') and unite(x.guid) ~= nil then m = m + 1 end
        end
    end
    R('RESTANTES', { m })
end

-- ==== VERSION 8 : la guerre réelle ( 02/10 ) ==========================================================================

local function vivante(numero)
    local e = registre()[numero]
    if e == nil then return nil, nil end
    return e, unite(e.guid)
end

-- Remplir le dépôt d'une unité HMT ( aérodrome, dépôt de munitions d'une vraie base ) avec N « packs » d'un chargement :
-- ScenEdit_FillMagsForLoadout ajoute N fois les armes du chargement ( sonde du 02/10 : 4 packs du F-16 7453 = 16
-- AIM-120C-5, 8 AIM-9X, 8 réservoirs ). Rend ARME numéro loadout packs lignes_réussies, ou ABSENT numéro.
function HMT_armer(R, ...)
    local t = { ... }
    if #t % 3 ~= 0 then error('HMT_armer : numéro, loadout, packs par dépôt') end
    for i = 1, #t, 3 do
        local k, lo, n = t[i], t[i + 1], t[i + 2]
        local e, u = vivante(k)
        if u == nil then
            R('ABSENT', { k })
        else
            local ok, r = pcall(ScenEdit_FillMagsForLoadout, { guid = e.guid, loadoutid = lo, quantity = n })
            local reussi = 0
            if ok and type(r) == 'table' then
                for _, ligne in pairs(r) do
                    if string.find(tostring(ligne), 'Successfully', 1, true) then reussi = reussi + 1 end
                end
            end
            R('ARME', { k, lo, n, reussi })
        end
    end
end

-- Les stocks des magasins : STOCK numéro arme courant capacité, pour chaque arme de chaque magasin.
function HMT_stocks(R, ...)
    for _, k in ipairs({ ... }) do
        local e, u = vivante(k)
        if u == nil then
            R('ABSENT', { k })
        else
            local n = 0
            for _, m in pairs(u.magazines or {}) do
                for _, w in pairs(m.mag_weapons or {}) do
                    R('STOCK', { k, w.wpn_dbid, w.wpn_current or 0, w.wpn_maxcap or 0 })
                    n = n + 1
                end
            end
            R('MAGASINS', { k, n })
        end
    end
end

-- Les pertes et dépenses d'un camp, telles que CMO les compte ( VP_GetSide().losses / .expenditures ) :
-- PERTE camp type dbid nombre et DEPENSE camp type dbid nombre ( type = HMT_TYPES ; les dbid d'avions et
-- d'installations se recouvrent ). C'est le coût réel de la guerre, rendu à l'économie du moteur.
function HMT_bilan(R, camp)
    local cote = HMT_CAMPS[camp]
    if cote == nil then error('HMT_REFUS 1') end
    local s = VP_GetSide({ side = cote })
    local np, nd = 0, 0
    for _, x in pairs(s.losses or {}) do
        R('PERTE', { camp, HMT_TYPES[x.type] or 0, x.dbid or 0, x.count or 0 })
        np = np + 1
    end
    for _, x in pairs(s.expenditures or {}) do
        R('DEPENSE', { camp, HMT_TYPES[x.type] or 0, x.dbid or 0, x.count or 0 })
        nd = nd + 1
    end
    R('BILAN', { camp, np, nd })
end

-- Un réglage de doctrine du camp, par son index dans HMT_DOCTRINE ; la valeur est relue dans CMO.
function HMT_doctrine(R, camp, i, valeur)
    local cote, cle = HMT_CAMPS[camp], HMT_DOCTRINE[i]
    if cote == nil then error('HMT_REFUS 1') end
    if cle == nil then error('HMT_REFUS 9') end
    ScenEdit_SetDoctrine({ side = cote }, { [cle] = valeur })
    local d = ScenEdit_GetDoctrine({ side = cote }) or {}
    R('DOCTRINE', { camp, i, tonumber(d[cle]) or -1 })
end

-- Importer une vraie installation ( index dans HMT_INSTALLATIONS ) dans un camp. CMO crée ses éléments sous leurs noms
-- d'origine : HMT_adopter les numérote ensuite, dans un AUTRE passage ( comme une suppression, l'import peut n'être
-- visible qu'au passage suivant ).
function HMT_importer(R, camp, idx)
    local cote, fichier = HMT_CAMPS[camp], HMT_INSTALLATIONS[idx]
    if cote == nil then error('HMT_REFUS 1') end
    if fichier == nil then error('HMT_REFUS 10') end
    local n = ScenEdit_ImportInst(cote, fichier)
    R('IMPORTE', { camp, idx, tonumber(n) or -1 })
end

-- Numéroter HMT-<premier>, HMT-<premier + 1>… chaque unité du camp qui n'est pas encore HMT ( l'installation qu'on vient
-- d'importer : nos camps ne contiennent que des unités HMT ). Le groupe ( la base elle-même, dbid 0 ) est numéroté aussi :
-- c'est lui qui accueille les avions. Rend ADOPTE numéro dbid lat lon groupe ( 1 = groupe ).
-- Renommer = écrire la propriété name de l'unité ( sonde du 02/10 : ScenEdit_SetUnit{ newname } et { name } sont ignorés
-- sans erreur ). La liste du camp contient aussi des fantômes : des rafales de canon tirées, que GetUnit ne rend pas ;
-- on les saute.
function HMT_adopter(R, camp, premier)
    local cote = HMT_CAMPS[camp]
    if cote == nil then error('HMT_REFUS 1') end
    local reg = registre()
    local s = VP_GetSide({ side = cote })
    local k = premier
    for _, x in ipairs(s.units or {}) do
        local u = (not string.match(x.name or '', '^HMT%-%d+$')) and unite(x.guid) or nil
        if u ~= nil then
            if reg[k] ~= nil and unite(reg[k].guid) ~= nil then error('HMT_REFUS 3') end
            u.name = 'HMT-' .. k
            if u.name ~= 'HMT-' .. k then error('HMT_REFUS 11') end
            reg[k] = { guid = x.guid, camp = camp }
            local groupe = (u.type == 'Group') and 1 or 0
            R('ADOPTE', { k, u.dbid or 0, u.latitude or 0, u.longitude or 0, groupe })
            k = k + 1
        end
    end
    R('ADOPTES', { camp, premier, k - premier })
end

-- Les dégâts : ETAT numéro pourcentage_de_dégâts feu ( 0 / 1 ) inondation ( 0 / 1 ), ou ABSENT numéro.
function HMT_etats(R, ...)
    for _, k in ipairs({ ... }) do
        local e, u = vivante(k)
        if u == nil then
            R('ABSENT', { k })
        else
            local d = u.damage or {}
            local feu = (d.fires ~= nil and d.fires ~= 'NoFire') and 1 or 0
            local eau = (d.flood ~= nil and d.flood ~= 'NoFlooding') and 1 or 0
            R('ETAT', { k, tonumber(d.dp_percent_now or d.dp_percent) or 0, feu, eau })
        end
    end
end
