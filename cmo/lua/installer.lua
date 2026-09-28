-- installer.lua : pose le pont HMT dans le scénario ouvert. À lancer UNE fois, dans la console Lua de CMO :
--
--     ScenEdit_RunScript('hmt_pont/installer.lua')
--
-- puis sauvegarder le scénario ( Ctrl+S ) et laisser le temps s'écouler ( x1 ). Relancer ne crée pas de doublon :
-- l'ancien événement est retiré d'abord. Une seule ligne de console : le limiteur de la 1.10 ( 3 envois, puis un
-- toutes les 30 s ) ne gêne pas ; le pont lui-même ne passe jamais par la console.

ScenEdit_RunScript('hmt_pont/hmt_config.lua')
ScenEdit_RunScript('hmt_pont/hmt_pont.lua')

local EVENEMENT, DECLENCHEUR, ACTION = 'HMT_PONT', 'HMT_PONT_1s', 'HMT_PONT_tic'
-- = ACTION_EVENEMENT de cmo_labo.py, au caractère près ( la porte le vérifie ).
local SCRIPT = "if HMT_tic == nil then ScenEdit_RunScript('hmt_pont/hmt_config.lua') ScenEdit_RunScript('hmt_pont/hmt_pont.lua') end HMT_tic()"

local existants = {}
for _, s in ipairs(VP_GetSides() or {}) do existants[s.name] = true end
for _, nom in ipairs(HMT_CAMPS) do
    if not existants[nom] then ScenEdit_AddSide({ side = nom }) end
end

for _, e in ipairs(ScenEdit_GetEvents(1) or {}) do
    if e.description == EVENEMENT then ScenEdit_SetEvent(EVENEMENT, { mode = 'remove' }) end
end
pcall(ScenEdit_SetTrigger, { description = DECLENCHEUR, mode = 'remove' })
pcall(ScenEdit_SetAction, { description = ACTION, mode = 'remove' })

local ev = ScenEdit_SetEvent(EVENEMENT, { mode = 'add', IsRepeatable = true })
ScenEdit_SetTrigger({ mode = 'add', type = 'RegularTime', Interval = '0', name = DECLENCHEUR })   -- '0' = 1 s
ScenEdit_SetEventTrigger(ev.guid, { mode = 'add', name = DECLENCHEUR })
ScenEdit_SetAction({ mode = 'add', type = 'LuaScript', name = ACTION, ScriptText = SCRIPT })
ScenEdit_SetEventAction(ev.guid, { mode = 'add', name = ACTION })

-- La sonde : ce que le bac à sable de ce build laisse passer. 1 = présent.
local function a(x) if x ~= nil then return 1 end return 0 end
local sonde = string.format('SONDE %d %d %d %d %d %d', a(io), a(dofile), a(loadfile), a(load), a(os), HMT_lecteur())
ScenEdit_ExportInst(HMT_CAMPS[1], {}, { filename = 'hmt_sonde.inst', name = 'HMT', comment = sonde .. '\nFIN' })
HMT_battre()
print('HMT : pont posé ( événement ' .. EVENEMENT .. ' ), ' .. sonde .. ', build ' .. tostring(GetBuildNumber()))
