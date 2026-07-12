"""verifie ou apparait le slot jouable + s'il est dans l'eau."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
ls = env._query('private _u = (playableUnits select 0); diag_log format ["HARMATTAN_SPAWN n=%1 pos=%2 eau=%3", count playableUnits, getPosATL _u, surfaceIsWater (getPosATL _u)];', settle=1.0)
line = next((l for l in ls if "HARMATTAN_SPAWN" in l), "")
m = re.search(r"HARMATTAN_SPAWN (.+)", line)
print(m.group(1).strip() if m else "(rien lu)")
