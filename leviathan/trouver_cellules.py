#!/usr/bin/env python3
"""trouver_cellules — des emplacements de banc qui sont VRAIMENT du terrain plat et sec.

Motif : la sonde du 27/07 a pose 3 de ses 5 angles EN MER (altitude -22, -118, -146 m).
Les « 0 tir / 35 touches / MORT » de ces trois angles etaient de la NOYADE, pas de l'arc de
tir. Le banc Arma avait 2 cellules sur 4 en mer. Tous les chiffres qui en sortent sont nuls.

Critere d'un bon emplacement :
  - terre au centre
  - pas d'eau dans un rayon de 250 m (les attaquants partent a 170 m, dans n'importe quel azimut)
  - relief faible : ecart d'altitude < 8 m sur la couronne a 150 m (terrain de mesure, pas de vallon)
  - pas de batiment dans 120 m (on mesure l'arc de tir, pas le masquage)
"""
import sys
import json
import math

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
RAYON_SEC = 250.0
RAYON_REL = 150.0
DH_MAX = 8.0
BAT_R = 120.0


def bloc(pts):
    """SQF qui teste une liste de points et n'emet que ceux qui passent."""
    s = ["private _o = " + Q + Q + "; private _h0 = 0; private _ok = true; private _hmin = 0; private _hmax = 0; "]
    for (x, y) in pts:
        s.append("_ok = !(surfaceIsWater [" + str(x) + "," + str(y) + "]); ")
        s.append("if (_ok) then { _h0 = getTerrainHeightASL [" + str(x) + "," + str(y) + "]; "
                 "_hmin = _h0; _hmax = _h0; ")
        for a in range(0, 360, 45):
            ex = x + RAYON_SEC * math.sin(math.radians(a))
            ey = y + RAYON_SEC * math.cos(math.radians(a))
            s.append("if (surfaceIsWater [" + ("%.0f" % ex) + "," + ("%.0f" % ey) + "]) then { _ok = false }; ")
            rx = x + RAYON_REL * math.sin(math.radians(a))
            ry = y + RAYON_REL * math.cos(math.radians(a))
            s.append("private _h = getTerrainHeightASL [" + ("%.0f" % rx) + "," + ("%.0f" % ry) + "]; "
                     "if (_h < _hmin) then {_hmin = _h}; if (_h > _hmax) then {_hmax = _h}; ")
        s.append("if (_hmax - _hmin > " + str(DH_MAX) + ") then { _ok = false }; ")
        s.append("if (_ok && {count (nearestTerrainObjects [[" + str(x) + "," + str(y) + ",0], "
                 "[" + Q + "HOUSE" + Q + "," + Q + "BUILDING" + Q + "], " + str(BAT_R) + "]) > 0}) then { _ok = false }; ")
        s.append("if (_ok) then { _o = _o + format [" + Q + P + "1,"
                 + P + "2," + P + "3;" + Q + ", " + str(x) + ", " + str(y) + ", round _h0] }; ")
        s.append("}; ")
    s.append("(format [" + Q + "G " + P + "1" + Q + ", _o]) call HMT_EMIT;")
    return "".join(s)


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    bons = []
    try:
        grille = [(x, y) for x in range(3000, 25001, 1000) for y in range(3000, 25001, 1000)]
        # tri par proximite du centre de l ile pour tomber vite sur les plaines
        lot = 40
        for i in range(0, len(grille), lot):
            pts = grille[i:i + lot]
            r = b.query(bloc(pts), r"G (\S*)", want=1, timeout=60)
            if not r:
                print("  lot %d : PAS DE REPONSE" % (i // lot), flush=True)
                continue
            got = r[-1].group(1).strip(";")
            for item in got.split(";"):
                p = item.split(",")
                if len(p) == 3:
                    bons.append((int(p[0]), int(p[1]), int(p[2])))
            print("  lot %2d/%d  (%d..%d)  retenus cumules : %d"
                  % (i // lot + 1, (len(grille) + lot - 1) // lot, i, i + len(pts), len(bons)), flush=True)
    finally:
        try:
            b.close()
        except Exception:
            pass

    print("")
    print("=== %d emplacements plats, secs, degages ===" % len(bons))
    # on choisit une SERIE de cellules espacees d au moins 700 m
    bons.sort(key=lambda t: (t[0], t[1]))
    serie = []
    for (x, y, h) in bons:
        if all(math.hypot(x - sx, y - sy) >= 700.0 for (sx, sy, _) in serie):
            serie.append((x, y, h))
    print("=== %d cellules mutuellement espacees de 700 m ===" % len(serie))
    for (x, y, h) in serie[:20]:
        print("   %6d %6d  alt %3d" % (x, y, h))
    json.dump({"tous": bons, "serie": serie},
              open("/home/younes/arma3-marl/leviathan/cellules_altis.json", "w"), indent=1)
    print("-> leviathan/cellules_altis.json")
    print("TROUVERCELL_DONE")


if __name__ == "__main__":
    main()
