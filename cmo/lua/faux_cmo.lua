-- faux_cmo.lua : un faux Command pour la porte ( porte_cmo.py ). Il imite ce que hmt_pont.lua et installer.lua
-- appellent, rien de plus. Les fichiers passent par PY_ecrire ( faux_cmo.py écrit le même JSON que CMO ).
-- Il ne prouve que la plomberie et le Lua du pont ; ce que CMO fait vraiment, seul le banc pontcmo le prouve.

FAUX = { camps = {}, unites = {}, n_guid = 0, temps = 1790000000, build = 'v1.10 - Build 1900.20',
         dbid_refuse = -1, runscript_leve = false, a_retirer = {},
         evenements = {}, declencheurs = {}, actions = {},
         -- v8 : chargements ( loadout -> { { arme, n } } ), fichiers .inst ( nom -> { { dbid, nom, lat, lon } } ),
         -- pertes et dépenses par camp, doctrines par camp, renommage refusé ( essai de mutant )
         loadouts = {}, fichiers_inst = {}, bilans = {}, doctrines = {}, renommer_refuse = false }

local function guid()
    FAUX.n_guid = FAUX.n_guid + 1
    return string.format('faux-%06d', FAUX.n_guid)
end

local function copie(u)
    local t = {}
    for k, v in pairs(u) do t[k] = v end
    return t
end

function VP_GetSides()
    local t = {}
    for i, s in ipairs(FAUX.camps) do t[i] = { name = s.name, guid = s.guid } end
    return t
end

function ScenEdit_AddSide(t)
    local s = { name = t.side or t.name, guid = guid() }
    table.insert(FAUX.camps, s)
    return copie(s)
end

function VP_GetSide(t)
    for _, s in ipairs(FAUX.camps) do
        if s.name == t.side or s.guid == t.side then
            local us = {}
            for _, u in pairs(FAUX.unites) do
                if u.side == s.name then us[#us + 1] = { name = u.name, guid = u.guid } end
            end
            local b = FAUX.bilans[s.name] or {}
            return { name = s.name, guid = s.guid, units = us, losses = b.losses or {}, expenditures = b.expenditures or {} }
        end
    end
    error('side not found')
end

function ScenEdit_AddUnit(t)
    local camp = nil
    for _, s in ipairs(FAUX.camps) do if s.name == t.side then camp = s end end
    if camp == nil or type(t.dbid) ~= 'number' or t.dbid <= 0 or t.dbid == FAUX.dbid_refuse then return nil end
    local la, lo = t.latitude, t.longitude
    if t.base then                                   -- posé sur une base : il est là où elle est, au sol
        local b = FAUX.unites[t.base]
        if b == nil or b.side ~= t.side then return nil end
        la, lo = b.latitude, b.longitude
    elseif la == nil or lo == nil then
        return nil
    end
    local u = { guid = guid(), name = t.unitname, side = t.side, type = t.type, dbid = t.dbid, base = t.base,
                latitude = la, longitude = lo, altitude = t.altitude or 0, magazines = {}, loadoutdbid = t.loadoutid,
                damage = { dp_percent_now = 0, fires = 'NoFire', flood = 'NoFlooding' } }
    FAUX.unites[u.guid] = u
    return copie(u)
end

-- Comme CMO : un objet dont on lit les champs, et dont la propriété name s'écrit ( le seul renommage qui marche en 1.10,
-- sonde du 02/10 ) ; les autres écritures ne touchent pas l'unité.
function ScenEdit_GetUnit(t)
    local u = t.guid and FAUX.unites[t.guid]
    if u == nil and t.unitname then
        for _, x in pairs(FAUX.unites) do if x.name == t.unitname then u = x end end
    end
    if u == nil or u.fantome then return nil end
    local c = copie(u)
    c.name = nil
    return setmetatable(c, {
        __index = function(_, k)
            if k == 'name' then return u.name end
            if k == 'ascontact' then                      -- comme CMO 1.10 : les camps qui la voient ( tous, sauf caché )
                local t = {}
                for _, s in ipairs(FAUX.camps) do
                    if s.name ~= u.side and not FAUX.caches[s.name .. '/' .. u.guid] then
                        local cg = 'C-' .. s.guid .. '-' .. u.guid
                        FAUX.contacts[cg] = { unite = u.guid, side = s.name }
                        t[#t + 1] = { guid = cg, name = 'contact', side = s.guid }
                    end
                end
                return t
            end
        end,
        __newindex = function(_, k, v) if k == 'name' and not FAUX.renommer_refuse then u.name = v end end })
end

FAUX.caches, FAUX.contacts, FAUX.classif = {}, {}, {}
function ScenEdit_GetContact(t)
    local c = FAUX.contacts[t.guid]
    if c == nil or c.side ~= t.side then return nil end
    local u = FAUX.unites[c.unite]
    if u == nil then return nil end
    return { guid = t.guid, classificationlevel = FAUX.classif[t.side .. '/' .. u.guid] or 4, age = 10,
             latitude = u.latitude, longitude = u.longitude, areaofuncertainty = {} }
end

function ScenEdit_SetUnit(t)
    local u = FAUX.unites[t.guid]
    if u == nil then error('unit not found') end
    if t.course and t.course[1] then u.latitude, u.longitude = t.course[1].latitude, t.course[1].longitude end
    return copie(u)
end

-- Comme CMO 1.10 ( sonde du 29/09 ) : la suppression est acceptée tout de suite, appliquée à la fin du passage.
function ScenEdit_DeleteUnit(t)
    if t.guid and FAUX.unites[t.guid] then
        table.insert(FAUX.a_retirer, t.guid)
        return true
    end
    return false
end

-- Missions : l'avion affecté à une patrouille se trouve, au passage suivant, au centre de sa zone ( l'IA de CMO
-- l'y mènerait ; le faux ne vole pas ).
FAUX.rp, FAUX.missions = {}, {}
function ScenEdit_AddReferencePoint(t) FAUX.rp[t.side .. '/' .. t.name] = { lat = t.latitude, lon = t.longitude } return copie(t) end
function ScenEdit_SetReferencePoint(t)
    local p = FAUX.rp[t.side .. '/' .. t.name]
    if p == nil then error('reference point not found') end
    p.lat, p.lon = t.latitude, t.longitude
    return copie(t)
end
function ScenEdit_GetMission(side, nom)
    local m = FAUX.missions[side .. '/' .. nom]
    if m == nil then return nil end
    return setmetatable({ name = nom, side = side }, {
        __index = function(_, k) if k == 'Phase' then return m.Phase end end,
        __newindex = function(_, k, v) if k == 'Phase' then m.Phase = v end end })
end
function ScenEdit_AddMission(side, nom, genre, opts)
    FAUX.missions[side .. '/' .. nom] = { side = side, genre = genre, type = opts.type, zone = opts.zone, unites = {},
                                          cibles = {}, Phase = (genre == 'Strike') and 30 or 20 }
    return { name = nom, side = side }
end
-- Comme CMO 1.10 : l'affectation de cible se fait par guid ( par nom : rien ) ; la mission rendue par GetMission laisse
-- écrire sa phase ( m.Phase = 20 ).
function ScenEdit_AssignUnitAsTarget(g, nom)
    local u = FAUX.unites[g]
    if u == nil then return {} end
    for cle, m in pairs(FAUX.missions) do
        if m.genre == 'Strike' and m.side ~= u.side and cle == m.side .. '/' .. nom then
            m.cibles[#m.cibles + 1] = g
            return { g }
        end
    end
    error('mission not found')
end
function ScenEdit_SetMission(side, nom, t)
    local m = FAUX.missions[side .. '/' .. nom]
    if m == nil then return nil end
    for k, v in pairs(t) do m[k] = v end
    return { name = nom, side = side }
end

function ScenEdit_DeleteMission(side, nom)
    local m = FAUX.missions[side .. '/' .. nom]
    if m == nil then error('mission not found') end
    FAUX.missions[side .. '/' .. nom] = nil
    for _, u in pairs(FAUX.unites) do
        if u.side == side and u.mission == nom then u.mission, u.escorte = nil, nil end
    end
    return true
end

function ScenEdit_AssignUnitToMission(guid, nom, escorte)
    local u = FAUX.unites[guid]
    if u == nil then return false end
    local m = FAUX.missions[u.side .. '/' .. nom]
    if m == nil then return false end
    u.mission = nom
    u.escorte = escorte == true
    return true
end

-- Comme CMO 1.10 ( sonde du 02/10 ) : par guid, rend false ; par nom, rend true, et l'avion n'a le chargement que si le
-- dépôt de sa base contient ses armes ( sinon chargement 3, sans armes ).
function ScenEdit_SetLoadout(t)
    if t.UnitName == nil then return false end
    local u
    for _, x in pairs(FAUX.unites) do if x.name == t.UnitName then u = x end end
    if u == nil then error('unit not found') end
    local base = u.base and FAUX.unites[u.base]
    local stock = {}
    for _, x in pairs(FAUX.unites) do
        if base and x.side == base.side and math.abs(x.latitude - base.latitude) < 0.05 and math.abs(x.longitude - base.longitude) < 0.05 then
            for _, m in ipairs(x.magazines or {}) do
                for _, w in ipairs(m.mag_weapons or {}) do stock[w.wpn_dbid] = (stock[w.wpn_dbid] or 0) + w.wpn_current end
            end
        end
    end
    local complet = true
    for _, a in ipairs(FAUX.loadouts[t.LoadoutID] or {}) do
        if (stock[a[1]] or 0) < a[2] then complet = false end
    end
    u.loadoutdbid = complet and t.LoadoutID or 3
    return true
end
local function voler()
    for _, u in pairs(FAUX.unites) do
        local m = u.mission and FAUX.missions[u.side .. '/' .. u.mission]
        if m and m.zone then
            local la, lo = 0, 0
            for _, n in ipairs(m.zone) do local p = FAUX.rp[u.side .. '/' .. n] la, lo = la + p.lat, lo + p.lon end
            u.latitude, u.longitude = la / #m.zone, lo / #m.zone
            if u.type == 'Air' then u.altitude = 8000 end   -- en mission, il vole ; posé sur sa base, il reste à 0
        elseif m and m.genre == 'Strike' and m.Phase == 20 and #m.cibles > 0 then
            -- une frappe ACTIVE mène l'avion sur sa première cible ( une frappe « OnHold » le laisse au parking, comme CMO )
            local c = FAUX.unites[m.cibles[1]]
            if c then u.latitude, u.longitude = c.latitude, c.longitude end
            if u.type == 'Air' then u.altitude = 8000 end
        end
    end
end
FAUX.voler = voler

function SetScenarioMessageLogPath(p) FAUX.journal = p end

FAUX.postures = {}
function ScenEdit_SetSidePosture(a, b, p) FAUX.postures[a .. '>' .. b] = p end
function ScenEdit_GetSidePosture(a, b) return FAUX.postures[a .. '>' .. b] or 'N' end

function GetBuildNumber() return FAUX.build end
function ScenEdit_CurrentTime() return FAUX.temps end

function ScenEdit_ExportInst(side, liste, f)
    PY_ecrire(f.filename, f.comment or '')
    return 0
end

function ScenEdit_GetEvents(n)
    local t = {}
    for _, e in ipairs(FAUX.evenements) do t[#t + 1] = { description = e.name, guid = e.guid } end
    return t
end

function ScenEdit_SetEvent(nom, t)
    if t.mode == 'add' then
        local e = { name = nom, guid = guid(), repetable = t.IsRepeatable, declencheurs = {}, actions = {} }
        table.insert(FAUX.evenements, e)
        return copie(e)
    end
    if t.mode == 'remove' then
        for i, e in ipairs(FAUX.evenements) do
            if e.name == nom or e.guid == nom then
                table.remove(FAUX.evenements, i)
                return true
            end
        end
    end
end

local function evenement(g)
    for _, e in ipairs(FAUX.evenements) do if e.guid == g or e.name == g then return e end end
    error('event not found')
end

function ScenEdit_SetTrigger(t)
    if t.mode == 'add' then FAUX.declencheurs[t.name] = copie(t) return copie(t) end
    if t.mode == 'remove' then FAUX.declencheurs[t.description] = nil return true end
end

function ScenEdit_SetAction(t)
    if t.mode == 'add' then FAUX.actions[t.name] = copie(t) return copie(t) end
    if t.mode == 'remove' then FAUX.actions[t.description] = nil return true end
end

function ScenEdit_SetEventTrigger(g, t) table.insert(evenement(g).declencheurs, t.name) end
function ScenEdit_SetEventAction(g, t) table.insert(evenement(g).actions, t.name) end

-- RunScript lit sous Lua/ de la racine. Il garde sa propre copie de loadfile : la porte retire loadfile pour
-- imiter un bac à sable plus strict, et RunScript doit alors rester le seul lecteur.
-- FAUX.runscript_leve imite un RunScript qui lève sur un fichier absent au lieu de rendre nil.
local charger = loadfile
function ScenEdit_RunScript(rel)
    local f = charger(FAUX_BASE .. 'Lua/' .. rel)
    if f == nil then
        if FAUX.runscript_leve then error('Lua file not found: ' .. rel) end
        return nil
    end
    f()
    return true
end

-- Un passage : l'action de chaque événement RegularTime, comme CMO toutes les secondes de jeu. CMO compile
-- l'action lui-même : le faux garde sa copie de load, que la porte retire au Lua du pont.
local compiler = load
function FAUX_passer()
    for _, e in ipairs(FAUX.evenements) do
        for _, dn in ipairs(e.declencheurs) do
            local d = FAUX.declencheurs[dn]
            if d and d.type == 'RegularTime' then
                for _, an in ipairs(e.actions) do
                    local a = FAUX.actions[an]
                    if a and a.type == 'LuaScript' then assert(compiler(a.ScriptText))() end
                end
            end
        end
    end
    for _, g in ipairs(FAUX.a_retirer) do FAUX.unites[g] = nil end
    FAUX.voler()
    FAUX.a_retirer = {}
    FAUX.temps = FAUX.temps + 1
end

function FAUX_detruire(numero)
    for g, u in pairs(FAUX.unites) do
        if u.name == 'HMT-' .. numero then FAUX.unites[g] = nil end
    end
end

function FAUX_compter()
    local k = 0
    for _, u in pairs(FAUX.unites) do if not u.fantome then k = k + 1 end end
    return k
end

-- Un rechargement de scénario : unités et événements restent ( ils sont dans la sauvegarde ), les globales Lua non.
function FAUX_recharger()
    HMT_tic, HMT_n, HMT_coeur, HMT_unites, HMT_attendu, HMT_commande = nil, nil, nil, nil, nil, nil
end

-- ==== v8 : magasins, bilans, doctrine, import de vraies installations, dégâts =========================================
local function trouver(t)
    local u = t.guid and FAUX.unites[t.guid]
    if u == nil and t.unitname then
        for _, x in pairs(FAUX.unites) do if x.name == t.unitname then u = x end end
    end
    return u
end

local function ajouter(u, arme, n)
    if #u.magazines == 0 then u.magazines[1] = { mag_dbid = 1185, mag_name = 'Munitions', mag_capacity = 10000, mag_weapons = {} } end
    local m = u.magazines[1]
    for _, w in ipairs(m.mag_weapons) do
        if w.wpn_dbid == arme then w.wpn_current = w.wpn_current + n return end
    end
    m.mag_weapons[#m.mag_weapons + 1] = { wpn_dbid = arme, wpn_current = n, wpn_maxcap = 10000 }
end

-- Comme CMO 1.10 ( sonde du 02/10 ) : une table de textes, une ligne « Successfully added » par arme du chargement.
function ScenEdit_FillMagsForLoadout(t)
    local u = trouver(t)
    if u == nil then error('unit not found') end
    local lignes = { 'Attempting to add ' .. t.quantity .. 'x packs of loadout: #' .. t.loadoutid }
    for _, a in ipairs(FAUX.loadouts[t.loadoutid] or {}) do
        ajouter(u, a[1], a[2] * t.quantity)
        lignes[#lignes + 1] = 'Successfully added ' .. (a[2] * t.quantity) .. 'x stores of type: ' .. a[1]
    end
    return lignes
end

function ScenEdit_AddWeaponToUnitMagazine(t)
    local u = trouver(t)
    if u == nil then error('unit not found') end
    ajouter(u, t.wpn_dbid, t.number)
    return t.number
end

function ScenEdit_SetDoctrine(sel, t)
    local d = FAUX.doctrines[sel.side] or {}
    for k, v in pairs(t) do d[k] = v end
    FAUX.doctrines[sel.side] = d
    return true
end
function ScenEdit_GetDoctrine(sel) return FAUX.doctrines[sel.side] or {} end

-- Un fichier .inst : ses éléments sous leurs noms d'origine, plus le groupe ( la base ), comme CMO ; rend le nombre
-- d'éléments ( 92 pour Šiauliai 2024, le groupe en plus ).
function ScenEdit_ImportInst(side, fichier)
    local membres = FAUX.fichiers_inst[fichier]
    if membres == nil then error('file not found: ' .. fichier) end
    local g = { guid = guid(), name = fichier, side = side, type = 'Group', dbid = 0, latitude = membres[1][3],
                longitude = membres[1][4], altitude = 0, magazines = {}, damage = { dp_percent_now = 0, fires = 'NoFire', flood = 'NoFlooding' } }
    FAUX.unites[g.guid] = g
    local r = { guid = guid(), name = '20mm/85 M61A1 Vulcan Burst [100 rnds]', side = side, type = 'Weapon', dbid = 0,
                latitude = 0, longitude = 0, fantome = true }
    FAUX.unites[r.guid] = r
    for _, m in ipairs(membres) do
        local u = { guid = guid(), name = m[2], side = side, type = 'Facility', dbid = m[1], latitude = m[3], longitude = m[4],
                    altitude = 0, magazines = {}, damage = { dp_percent_now = 0, fires = 'NoFire', flood = 'NoFlooding' } }
        FAUX.unites[u.guid] = u
    end
    return #membres
end

-- Comme CMO 1.10 ( sonde du 02/10 ) : points restants en nombres, pourcentage en TEXTE à la virgule.
function FAUX_endommager_cmo(numero, dp, startdp)
    for _, u in pairs(FAUX.unites) do
        if u.name == 'HMT-' .. numero then
            local p = (startdp - dp) / startdp * 100
            u.damage = { dp = dp, startdp = startdp, dp_percent = string.gsub(string.format('%.1f', p), '%.', ','),
                         dp_percent_now = (string.gsub(string.format('%.1f', p), '%.', ',')), fires = 'NoFire', flood = 'NoFlooding' }
        end
    end
end

function FAUX_endommager(numero, pct, feu)
    for _, u in pairs(FAUX.unites) do
        if u.name == 'HMT-' .. numero then
            u.damage.dp_percent_now = pct
            if feu then u.damage.fires = 'MinorFire' end
        end
    end
end

function ScenEdit_SetStartTime(t) FAUX.duree = t.Duration return FAUX.temps end
