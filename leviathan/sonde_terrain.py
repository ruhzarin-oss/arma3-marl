#!/usr/bin/env python3
"""sonde_terrain — LE TERRAIN SOUS LE BANC EST-IL DE LA TERRE ?

Avant d'expliquer un 0 %, on verifie l'instrument. Le banc Arma et la sonde d'arc posent
leurs cellules a (23000, 17400) et vers l'est. Sur Altis, l'est est en grande partie de la
MER. Un soldat pose dans l'eau se noie : il meurt sans qu'aucun coup ne soit tire, ce qui
donne exactement « 0 % pris, 3,3 pertes sur 4 » et « 35 touches, 0 tir ».

On demande au moteur : eau ou terre, et a quelle altitude, en chaque point utilise.
"""
import sys
import json

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)

PTS = []
# cellules du banc Arma : zone 23000,17400 pas 900, 4 cellules
for k in range(4):
    PTS.append(("banc_c%d" % k, 23000 + 900 * k, 17400))
# cellules de la sonde d'arc : pas 700, 5 cellules
for k in range(5):
    PTS.append(("arc_c%d" % k, 23000 + 700 * k, 17400))
# reperes connus
PTS.append(("pyrgos", 16781, 12604))
PTS.append(("athira", 13993, 18709))
PTS.append(("gravia", 14480, 17614))


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    try:
        parts = []
        for nom, x, y in PTS:
            parts.append(
                "_o = _o + format [" + Q + P + "1=" + P + "2/" + P + "3;" + Q + ", "
                + Q + nom + Q + ", "
                "(if (surfaceIsWater [" + str(x) + "," + str(y) + "]) then {" + Q + "EAU" + Q + "} else {" + Q + "terre" + Q + "}), "
                "round (getTerrainHeightASL [" + str(x) + "," + str(y) + "])]; ")
        sqf = ("private _o = " + Q + Q + "; " + "".join(parts)
               + "(format [" + Q + "T " + P + "1" + Q + ", _o]) call HMT_EMIT;")
        r = b.query(sqf, r"T (\S+)", want=1, timeout=30)
        if not r:
            print("PAS DE REPONSE")
            return 1
        res = {}
        print("%-10s %8s %8s" % ("point", "surface", "alt"))
        for item in r[-1].group(1).strip(";").split(";"):
            if "=" not in item:
                continue
            nom, rest = item.split("=", 1)
            surf, alt = rest.split("/")
            res[nom] = {"surface": surf, "alt": int(alt)}
            print("%-10s %8s %8s" % (nom, surf, alt))
        json.dump(res, open("/home/younes/arma3-marl/leviathan/sonde_terrain.json", "w"), indent=1)
        eau = [k for k, v in res.items() if v["surface"] == "EAU"]
        print("")
        if eau:
            print("!! POINTS EN MER : %s" % ", ".join(eau))
        else:
            print("tous les points sont sur terre")
        print("SONDETERRAIN_DONE")
        return 0
    finally:
        try:
            b.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
