"""ou est REELLEMENT le joueur connecte (vs le slot)."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = ('diag_log format ["HARMATTAN_PC %1", count allPlayers]; '
       '{ diag_log format ["HARMATTAN_PP pos=%1 eau=%2 vivant=%3", getPosATL _x, surfaceIsWater (getPosATL _x), alive _x]; } forEach allPlayers;')
ls = env._query(sqf, settle=1.5)
for l in ls:
    if "HARMATTAN_PC" in l or "HARMATTAN_PP" in l:
        m = re.search(r"HARMATTAN_P[CP] (.+)", l)
        if m: print(m.group(1).strip())
