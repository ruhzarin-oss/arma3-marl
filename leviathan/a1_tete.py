#!/usr/bin/env python3
"""a1_tete — TETE DE CHAINE. Rien ne se mesure avant que l'instrument soit prouve.

Trois epreuves, dans cet ordre. La premiere qui echoue arrete la chaine Arma et le DIT.

  1. LE PONT REPOND            une requete simple, une reponse.
  2. LE CANARI DU CAPTEUR      un tir FORCE qui DOIT etre enregistre. On ne conclut jamais
                               a un zero sans avoir prouve que le compteur sait compter.
  3. LA TERRE FERME            chaque cellule du banc est verifiee : pas d'eau au centre ni
                               sur la couronne a 250 m, relief faible, pas de bati a 120 m.
                               Entree au rituel le 27/07, apres qu'une sonde a pose trois de
                               ses cinq angles EN MER (-22, -118, -146 m) et qu'un banc a
                               noye la moitie de ses episodes. Les zeros etaient des noyades.

Sortie 0 = la chaine peut mesurer. Sortie 2 = elle ne doit pas.
"""
import sys
import time
import json
import math

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"


def fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main():
    rap = {"quand": time.strftime("%Y-%m-%d %H:%M"), "epreuves": {}}
    b = NativeBridge(port=theatre.use("altis").PORT)
    try:
        # ---------------------------------------------------------- 1. LE PONT
        r = b.query("(format [" + Q + "E monde=" + P + "1 unites=" + P + "2 groupes=" + P + "3" + Q
                    + ", worldName, count allUnits, count allGroups]) call HMT_EMIT;",
                    r"E monde=(\S+) unites=(\d+) groupes=(\d+)", want=1, timeout=30)
        if not r:
            print("1. PONT : MUET  -> la chaine Arma ne mesure pas.", flush=True)
            rap["epreuves"]["pont"] = {"ok": False}
            json.dump(rap, open(LEV + "/a1_tete.json", "w"), indent=1)
            return 2
        print("1. PONT : %s" % r[-1].group(0), flush=True)
        rap["epreuves"]["pont"] = {"ok": True, "monde": r[-1].group(1),
                                   "unites": int(r[-1].group(2)), "groupes": int(r[-1].group(3))}

        # ---------------------------------------------------------- 2. LE CANARI
        # Un tireur, une cible a 30 m, feu FORCE. Le compteur de tirs ET le compteur
        # d'impacts (filtre par source, dedouble par tick) doivent tous deux bouger.
        CEL = json.load(open(LEV + "/cellules_altis.json"))["serie"]
        cx, cy = CEL[0][0], CEL[0][1]
        c = ("if (!isNil " + Q + "HMT_K" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_K }; "
             "HMT_K = []; HMT_KT = 0; HMT_KI = 0; HMT_KLT = 0; "
             "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "
             "private _g = createGroup east; private _h = createGroup west; "
             "HMT_KD = _g createUnit [" + Q + "O_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
             "HMT_KC = _h createUnit [" + Q + "B_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy + 30) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
             "HMT_KD setPosATL [" + str(cx) + "," + str(cy) + ",0]; HMT_KD setDir 0; HMT_KD setSkill 0.6; "
             "HMT_KC setPosATL [" + str(cx) + "," + str(cy + 30) + ",0]; HMT_KC setDir 180; "
             "{ _x setUnitPos " + Q + "UP" + Q + "; _x setBehaviour " + Q + "COMBAT" + Q + "; "
             "  _x setCombatMode " + Q + "RED" + Q + "; _x disableAI " + Q + "PATH" + Q + "; "
             "  _x enableSimulation true; _x enableDynamicSimulation false; } forEach [HMT_KD, HMT_KC]; "
             "HMT_KD allowDamage false; "                          # il doit survivre pour tirer
             "HMT_KD addEventHandler [" + Q + "Fired" + Q + ", { HMT_KT = HMT_KT + 1 }]; "
             "HMT_KC addEventHandler [" + Q + "HandleDamage" + Q + ", { "
             "  if (((_this select 3) isEqualTo HMT_KD) && {diag_tickTime - HMT_KLT > 0.05}) then { "
             "    HMT_KLT = diag_tickTime; HMT_KI = HMT_KI + 1 }; 0 }]; "
             "HMT_K pushBack HMT_KD; HMT_K pushBack HMT_KC; "
             "HMT_KD reveal [HMT_KC, 4]; HMT_KD doTarget HMT_KC; HMT_KD doFire HMT_KC; "
             "(format [" + Q + "CAN " + P + "1" + Q + ", count HMT_K]) call HMT_EMIT;")
        r = b.query(c, r"CAN (\d+)", want=1, timeout=90)
        if not r:
            print("2. CANARI : mise en place SANS REPONSE -> la chaine ne mesure pas.", flush=True)
            rap["epreuves"]["canari"] = {"ok": False, "raison": "mise en place muette"}
            json.dump(rap, open(LEV + "/a1_tete.json", "w"), indent=1)
            return 2
        tirs = imp = 0
        for k in range(6):
            time.sleep(5)
            b.send("if (alive HMT_KD && alive HMT_KC) then { HMT_KD reveal [HMT_KC, 4]; "
                   "HMT_KD doTarget HMT_KC; HMT_KD doFire HMT_KC; };", wait=False)
            rr = b.query("(format [" + Q + "KAN " + P + "1 " + P + "2" + Q + ", HMT_KT, HMT_KI]) call HMT_EMIT;",
                         r"KAN (\d+) (\d+)", want=1, timeout=30)
            if rr:
                tirs, imp = int(rr[-1].group(1)), int(rr[-1].group(2))
            print("   canari +%2ds : %d tirs, %d impacts (filtres par source, dedoubles)"
                  % (5 * (k + 1), tirs, imp), flush=True)
            if tirs > 0 and imp > 0:
                break
        b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_K; HMT_K = []; "
               "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
        ok_can = tirs > 0 and imp > 0
        rap["epreuves"]["canari"] = {"ok": bool(ok_can), "tirs": tirs, "impacts": imp}
        print("2. CANARI : %s (%d tirs, %d impacts)"
              % ("OK — le capteur compte" if ok_can else "ECHEC — le capteur est MUET", tirs, imp), flush=True)
        if not ok_can:
            json.dump(rap, open(LEV + "/a1_tete.json", "w"), indent=1)
            return 2

        # ---------------------------------------------------------- 3. LA TERRE FERME
        bons = []
        mauvais = []
        for (x, y, _h) in CEL:
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
                s.append("private _hh = getTerrainHeightASL [" + ("%.0f" % rx) + "," + ("%.0f" % ry) + "]; "
                         "if (_hh < _mn) then {_mn = _hh}; if (_hh > _mx) then {_mx = _hh}; ")
            s.append("private _nb = count (nearestTerrainObjects [[" + str(x) + "," + str(y) + ",0], "
                     "[" + Q + "HOUSE" + Q + "," + Q + "BUILDING" + Q + "], 120]); ")
            s.append("(format [" + Q + "T " + str(x) + " " + str(y) + " " + P + "1 " + P + "2 " + P + "3 " + P + "4" + Q
                     + ", (if (_ok) then {1} else {0}), round _h0, round (_mx - _mn), _nb]) call HMT_EMIT;")
            rr = b.query("".join(s), r"T (\d+) (\d+) (\d+) (-?\d+) (\d+) (\d+)", want=1, timeout=40)
            if not rr:
                mauvais.append([x, y, "muet"])
                continue
            g = rr[-1]
            sec, alt, dh, nb = int(g.group(3)), int(g.group(4)), int(g.group(5)), int(g.group(6))
            if sec == 1 and dh < 8 and nb == 0:
                bons.append([x, y, alt])
            else:
                mauvais.append([x, y, "eau=%d relief=%d bati=%d" % (1 - sec, dh, nb)])
        print("3. TERRE FERME : %d cellules certifiees, %d rejetees" % (len(bons), len(mauvais)), flush=True)
        for m in mauvais:
            print("     rejetee %6d %6d : %s" % (m[0], m[1], m[2]), flush=True)
        rap["epreuves"]["terre"] = {"ok": len(bons) >= 4, "certifiees": len(bons), "rejetees": mauvais}
        json.dump({"serie": bons}, open(LEV + "/cellules_altis.json", "w"), indent=1)
        json.dump(rap, open(LEV + "/a1_tete.json", "w"), indent=1)
        if len(bons) < 4:
            print("   moins de 4 cellules valides -> la chaine Arma ne mesure pas.", flush=True)
            return 2
        print("", flush=True)
        print("TETE DE CHAINE : LES TROIS EPREUVES PASSENT. On peut mesurer.", flush=True)
        print("A1_DONE", flush=True)
        return 0
    finally:
        fermer(b)


if __name__ == "__main__":
    sys.exit(main())
