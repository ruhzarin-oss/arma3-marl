"""diagnostic du curator (Zeus) du joueur : a-t-il un curator ? combien d'objets editables ? combien d'unites ?"""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = ('diag_log format ["HARMATTAN_AU allunits=%1 hmten=%2", count allUnits, (if (isNil "HMT_EN") then {-1} else {count HMT_EN})]; '
       '{ private _c = getAssignedCuratorLogic _x; '
       'diag_log format ["HARMATTAN_CUR hasCur=%1 editable=%2", !isNull _c, (if (isNull _c) then {-1} else {count curatorEditableObjects _c})]; '
       'if (!isNull _c) then { _c addCuratorEditableObjects [allUnits, true]; _c setCuratorCoef ["Place", 0]; }; '
       '} forEach allPlayers;')
ls = env._query(sqf, settle=1.5)
for tag in ["HARMATTAN_AU", "HARMATTAN_CUR"]:
    for l in ls:
        m = re.search(tag + r" (.+)", l)
        if m:
            print(tag.replace("HARMATTAN_", ""), ":", m.group(1).strip()[:60])
