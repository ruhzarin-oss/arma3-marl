"""donne au curator du joueur le catalogue d'addons + force toutes les unites editables (Zeus complet)."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = ('HMT_FULLZEUS = true; '
       '{ private _c = getAssignedCuratorLogic _x; '
       'if (!isNull _c) then { '
       '  _c addCuratorAddons (activatedAddons); '
       '  _c setCuratorCoef ["Place", 0]; _c setCuratorCoef ["Edit", 0]; _c setCuratorCoef ["Delete", 0]; _c setCuratorCoef ["Destroy", 0]; '
       '  _c addCuratorEditableObjects [allUnits, true]; '
       '  diag_log format ["HARMATTAN_FIX editable=%1 addons=%2", count curatorEditableObjects _c, count curatorAddons _c]; '
       '}; } forEach allPlayers;')
ls = env._query(sqf, settle=1.5)
m = next((re.search(r"HARMATTAN_FIX (.+)", l) for l in ls if "HARMATTAN_FIX" in l), None)
print("apres fix :", m.group(1).strip()[:60] if m else "(rien lu)")
