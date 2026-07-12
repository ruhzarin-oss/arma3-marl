"""relief_altis — grille FINE d'Altis (128x128) : altitude + classe de sol, en une passe. Sert au rendu
photo-realiste (relief ombre + couverture du sol). Ecrit staff/altis_relief.json {G,cell,size,H[[h]],S[[classe]]}.
Classes sol : 0 mer · 1 plage · 2 champ-vert · 3 broussaille-seche · 4 foret · 5 roche · 6 terre/sol · 7 marais."""
import re, json
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
G = 128
CELL = 30720.0 / G
CHUNK = 180

CLS = {"GdtSeabed": 0, "GdtBeach": 1, "GdtGrassGreen": 2, "GdtGrassWild": 2, "GdtMarsh": 7,
       "GdtGrassDry": 3, "GdtThorn": 3, "GdtDead": 3, "GdtForestPine": 4, "GdtStony": 5,
       "GdtDirt": 6, "GdtSoil": 6}


def cls(s):
    s = s.lstrip("#").strip('"')
    return CLS.get(s, 3)


env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", seed=0)
pts = [(gx, gy) for gy in range(G) for gx in range(G)]
H = [[-200] * G for _ in range(G)]
S = [[0] * G for _ in range(G)]
done = 0
for i in range(0, len(pts), CHUNK):
    chunk = pts[i:i + CHUNK]
    arr = "[" + ",".join("[%d,%d]" % (gx, gy) for gx, gy in chunk) + "]"
    sqf = ('{ private _g=_x; private _p=[(_g#0)*%f + %f, (_g#1)*%f + %f];\n'
           '  private _h=round getTerrainHeightASL _p; private _s=surfaceType _p;\n'
           '  diag_log format ["HARMATTAN_R %%1 %%2 %%3 %%4", _g#0, _g#1, _h, _s]; } forEach %s;\n'
           % (CELL, CELL / 2, CELL, CELL / 2, arr))
    for l in env._query(sqf, settle=2.0):
        m = re.search(r"HARMATTAN_R (\d+) (\d+) (-?\d+) (\S+)", l)
        if m:
            gx, gy, h = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 0 <= gx < G and 0 <= gy < G:
                H[gy][gx] = h
                S[gy][gx] = cls(m.group(4))
                done += 1
    print("%d/%d points" % (done, G * G), flush=True)
land = sum(1 for r in H for v in r if v > 0)
json.dump({"G": G, "cell": CELL, "size": 30720, "H": H, "S": S},
          open("/home/younes/arma3-marl/staff/altis_relief.json", "w"))
print("RELIEF FIN %dx%d : %d points | terre=%d mer=%d" % (G, G, done, land, G * G - land))
