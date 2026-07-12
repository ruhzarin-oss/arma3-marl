"""altis_terrain — grille d'altitude d'Altis (48x48) par chunks (pattern fiable) -> forme de l'ile (mer=h<=0).
Fond de la carte strategique. Ecrit staff/altis_terrain.json."""
import re, json
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
G = 48
CELL = 30720.0 / G
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
pts = [(gx, gy) for gy in range(G) for gx in range(G)]
grid = [[-50] * G for _ in range(G)]
done = 0
for i in range(0, len(pts), 120):
    chunk = pts[i:i + 120]
    arr = "[" + ",".join("[%d,%d]" % (gx, gy) for gx, gy in chunk) + "]"
    sqf = ('{ private _g=_x; diag_log format ["HARMATTAN_H %%1 %%2 %%3", _g#0, _g#1, round (getTerrainHeightASL [(_g#0)*%f + %f, (_g#1)*%f + %f])]; } forEach %s;'
           % (CELL, CELL / 2, CELL, CELL / 2, arr))
    ls = env._query(sqf, settle=2.2)
    for l in ls:
        m = re.search(r"HARMATTAN_H (\d+) (\d+) (-?\d+)", l)
        if m:
            gx, gy, h = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 0 <= gx < G and 0 <= gy < G:
                grid[gy][gx] = h; done += 1
json.dump({"G": G, "cell": CELL, "size": 30720, "grid": grid}, open("/home/younes/arma3-marl/staff/altis_terrain.json", "w"))
land = sum(1 for r in grid for v in r if v > 0)
print("grille %dx%d | %d points lus | terre=%d mer=%d" % (G, G, done, land, G * G - land))
