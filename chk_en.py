"""ou sont les 5 defenseurs (HMT_EN) + le joueur : terre ou eau ?"""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = ('if (!isNil "HMT_EN") then { { diag_log format ["HARMATTAN_EN pos=%1 eau=%2", getPosATL _x, surfaceIsWater (getPosATL _x)]; } forEach HMT_EN; }; '
       '{ diag_log format ["HARMATTAN_PL pos=%1 eau=%2 vivant=%3", getPosATL _x, surfaceIsWater (getPosATL _x), alive _x]; } forEach allPlayers;')
ls = env._query(sqf, settle=1.5)
for l in ls:
    for tag in ["HARMATTAN_EN", "HARMATTAN_PL"]:
        m = re.search(tag + r" (.+)", l)
        if m:
            print(tag.replace("HARMATTAN_", ""), ":", m.group(1).strip()[:55])
