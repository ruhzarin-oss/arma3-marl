-- faux_cmo.lua : un faux Command pour la porte ( porte_cmo.py ). Il imite ce que hmt_pont.lua et installer.lua
-- appellent, rien de plus. Les fichiers passent par PY_ecrire ( faux_cmo.py écrit le même JSON que CMO ).
-- Il ne prouve que la plomberie et le Lua du pont ; ce que CMO fait vraiment, seul le banc pontcmo le prouve.

FAUX = { camps = {}, unites = {}, n_guid = 0, temps = 1790000000, build = 'v1.10 - Build 1900.20',
         dbid_refuse = -1, runscript_leve = false,
         evenements = {}, declencheurs = {}, actions = {} }

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
            return { name = s.name, guid = s.guid, units = us }
        end
    end
    error('side not found')
end

function ScenEdit_AddUnit(t)
    local camp = nil
    for _, s in ipairs(FAUX.camps) do if s.name == t.side then camp = s end end
    if camp == nil or type(t.dbid) ~= 'number' or t.dbid <= 0 or t.dbid == FAUX.dbid_refuse then return nil end
    local u = { guid = guid(), name = t.unitname, side = t.side, type = t.type, dbid = t.dbid,
                latitude = t.latitude, longitude = t.longitude, altitude = t.altitude or 0 }
    FAUX.unites[u.guid] = u
    return copie(u)
end

function ScenEdit_GetUnit(t)
    local u = t.guid and FAUX.unites[t.guid]
    if u == nil and t.unitname then
        for _, x in pairs(FAUX.unites) do if x.name == t.unitname then u = x end end
    end
    if u == nil then return nil end
    return copie(u)
end

function ScenEdit_SetUnit(t)
    local u = FAUX.unites[t.guid]
    if u == nil then error('unit not found') end
    if t.course and t.course[1] then u.latitude, u.longitude = t.course[1].latitude, t.course[1].longitude end
    return copie(u)
end

function ScenEdit_DeleteUnit(t)
    if t.guid and FAUX.unites[t.guid] then
        FAUX.unites[t.guid] = nil
        return true
    end
    return false
end

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
    FAUX.temps = FAUX.temps + 1
end

function FAUX_detruire(numero)
    for g, u in pairs(FAUX.unites) do
        if u.name == 'HMT-' .. numero then FAUX.unites[g] = nil end
    end
end

function FAUX_compter()
    local k = 0
    for _ in pairs(FAUX.unites) do k = k + 1 end
    return k
end

-- Un rechargement de scénario : unités et événements restent ( ils sont dans la sauvegarde ), les globales Lua non.
function FAUX_recharger()
    HMT_tic, HMT_n, HMT_coeur, HMT_unites, HMT_attendu, HMT_commande = nil, nil, nil, nil, nil, nil
end
