"""probe_surf — sonde le vocabulaire de surfaces d'Altis (surfaceType) pour construire la table de couleurs."""
import re
from collections import Counter
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", seed=0)
pts = [(x, y) for x in range(1500, 30000, 2200) for y in range(1500, 30000, 2200)]  # ~14x14
cnt = Counter()
samp = {}
for i in range(0, len(pts), 110):
    arr = "[" + ",".join("[%d,%d]" % (x, y) for x, y in pts[i:i + 110]) + "]"
    sqf = ('{ private _h = round getTerrainHeightASL _x; private _s = surfaceType _x;\n'
           '  diag_log format ["HARMATTAN_S x=%1 y=%2 h=%3 s=%4", _x#0, _x#1, _h, _s]; } forEach ' + arr + ';\n')
    for l in env._query(sqf, settle=2.2):
        m = re.search(r"HARMATTAN_S x=(-?\d+) y=(-?\d+) h=(-?\d+) s=(\S+)", l)
        if m:
            s = m.group(4)
            cnt[s] += 1
            samp.setdefault(s, (int(m.group(1)), int(m.group(2)), int(m.group(3))))
print("surfaces distinctes :", len(cnt))
for s, c in cnt.most_common():
    print("%4d  %-30s  ex(x,y,h)=%s" % (c, s, samp[s]))
