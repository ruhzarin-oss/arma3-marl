#!/usr/bin/env python3
"""verifier_cellules — le moteur confirme, un point a la fois.

Le scan massif est mort de sa lourdeur : SQF trop long, zero reponse sur 14 lots.
Ici on ne verifie que les 24 finalistes choisis hors ligne, par lots de TROIS, avec des
requetes courtes. Chaque cellule doit passer quatre epreuves :
    - terre au centre
    - aucune eau sur la couronne a 250 m (8 azimuts) ni a 120 m
    - ecart d altitude < 8 m sur la couronne a 150 m
    - aucun batiment dans 120 m
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
LEV = "/home/younes/arma3-marl/leviathan"
CAND = json.load(open(LEV + "/cellules_altis_brut.json"))["serie"]


def sqf_un(x, y):
    s = ["private _ok = !(surfaceIsWater [" + str(x) + "," + str(y) + "]); ",
         "private _h0 = getTerrainHeightASL [" + str(x) + "," + str(y) + "]; ",
         "private _mn = _h0; private _mx = _h0; "]
    for ang in range(0, 360, 45):
        for R in (120.0, 250.0):
            ex = x + R * math.sin(math.radians(ang))
            ey = y + R * math.cos(math.radians(ang))
            s.append("if (surfaceIsWater [" + ("%.0f" % ex) + "," + ("%.0f" % ey) + "]) then {_ok = false}; ")
        rx = x + 150.0 * math.sin(math.radians(ang))
        ry = y + 150.0 * math.cos(math.radians(ang))
        s.append("private _h = getTerrainHeightASL [" + ("%.0f" % rx) + "," + ("%.0f" % ry) + "]; "
                 "if (_h < _mn) then {_mn = _h}; if (_h > _mx) then {_mx = _h}; ")
    s.append("private _nb = count (nearestTerrainObjects [[" + str(x) + "," + str(y) + ",0], "
             "[" + Q + "HOUSE" + Q + "," + Q + "BUILDING" + Q + "," + Q + "FOREST" + Q + "], 120]); ")
    s.append("(format [" + Q + "V " + str(x) + " " + str(y) + " " + P + "1 " + P + "2 " + P + "3 " + P + "4" + Q
             + ", (if (_ok) then {1} else {0}), round _h0, round (_mx - _mn), _nb]) call HMT_EMIT;")
    return "".join(s)


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    bons = []
    try:
        for k, (x, y, _h) in enumerate(CAND):
            r = b.query(sqf_un(x, y), r"V (\d+) (\d+) (\d+) (-?\d+) (\d+) (\d+)", want=1, timeout=40)
            if not r:
                print("  %6d %6d : PAS DE REPONSE" % (x, y), flush=True)
                continue
            g = r[-1]
            xx, yy = int(g.group(1)), int(g.group(2))
            sec, alt, dh, nb = int(g.group(3)), int(g.group(4)), int(g.group(5)), int(g.group(6))
            ok = sec == 1 and dh < 8 and nb == 0
            print("  %6d %6d  sec=%d alt=%4d relief=%3d bati=%3d  %s"
                  % (xx, yy, sec, alt, dh, nb, "RETENUE" if ok else "rejetee"), flush=True)
            if ok:
                bons.append([xx, yy, alt])
    finally:
        try:
            b.close()
        except Exception:
            pass
    print("")
    print("=== %d cellules certifiees ===" % len(bons))
    json.dump({"serie": bons}, open(LEV + "/cellules_altis.json", "w"), indent=1)
    print("-> cellules_altis.json")
    print("VERIFCELL_DONE")


if __name__ == "__main__":
    main()
