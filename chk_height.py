"""altitude + eau de plusieurs points candidats pour choisir un spawn franchement sur terre."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
PTS = [(12000, 21000), (11855, 21145), (12100, 20900), (12000, 20850), (12150, 21000), (11900, 20950)]
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
arr = "[" + ",".join("[" + str(p[0]) + "," + str(p[1]) + "]" for p in PTS) + "]"
sqf = '{ private _p=_x; diag_log format ["HARMATTAN_H %1 %2 %3 eau=%4", _p#0, _p#1, round (getTerrainHeightASL _p), surfaceIsWater [_p#0,_p#1,0]]; } forEach ' + arr + ';'
ls = env._query(sqf, settle=1.5)
for l in ls:
    m = re.search(r"HARMATTAN_H (\d+) (\d+) (-?\d+) eau=(\w+)", l)
    if m:
        print("(%s,%s) h=%sm eau=%s" % (m.group(1), m.group(2), m.group(3), m.group(4)))
