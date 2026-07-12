"""roads_altis — reseau routier d'Altis pour la carte d'etat-major. On balaie l'ile par TUILES (capture fiable) :
pour chaque tuile, nearRoads -> on garde les axes 'main road' + 'road' (on jette tracks/trails) -> on log la
position monde. Dedup 22m cote Python. Ecrit staff/altis_roads.json -> couche routes sous les objectifs.
  python roads_altis.py test   -> 1 tuile (Pyrgos) pour valider la capture."""
import re, json, sys
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
SIZE = 30720
T = 10                       # 10x10 tuiles
tile = SIZE / T
RAD = tile * 0.80            # couvre le coin de tuile (0.707*tile) + marge

env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", seed=0)


def scan_tile(cx, cy):
    sqf = ('private _rs = [%f,%f,0] nearRoads %f;\n'
           '{ private _i = getRoadInfo _x; private _t = toLower (_i select 0); private _p = getPosWorld _x;\n'
           '  if (_t in ["main road","road"]) then {\n'
           '    diag_log format ["HARMATTAN_RD t=%%1 x=%%2 y=%%3", _t, round (_p select 0), round (_p select 1)];\n'
           '  };\n'
           '} forEach _rs;\n'
           'diag_log "HARMATTAN_RDDONE";\n') % (cx, cy, RAD)
    ls = env._query(sqf, settle=2.5)
    out = []
    for l in ls:
        m = re.search(r"HARMATTAN_RD t=(.+?) x=(-?\d+) y=(-?\d+)", l)
        if m:
            out.append((m.group(1).strip(), int(m.group(2)), int(m.group(3))))
    return out


if len(sys.argv) > 1 and sys.argv[1] == "test":
    pts = scan_tile(16500, 16500)            # zone Pyrgos, dense en routes
    print("TEST tuile Pyrgos -> %d segments captures" % len(pts))
    for p in pts[:6]:
        print("  ", p)
    sys.exit(0)

seg = {}
for ty in range(T):
    for tx in range(T):
        cx = tx * tile + tile / 2
        cy = ty * tile + tile / 2
        for t, x, y in scan_tile(cx, cy):
            key = (round(x / 22) * 22, round(y / 22) * 22)
            if key not in seg:
                seg[key] = [key[0], key[1], 0 if t == "main road" else 1]
        print("tuile %d,%d -> cumul %d points" % (tx, ty, len(seg)), flush=True)
pts = list(seg.values())
main = sum(1 for p in pts if p[2] == 0)
json.dump({"size": SIZE, "roads": pts}, open("/home/younes/arma3-marl/staff/altis_roads.json", "w"))
print("ROUTES Altis : %d points (dont %d 'main road'), dedup 22m" % (len(pts), main))
