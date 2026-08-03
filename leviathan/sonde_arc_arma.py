#!/usr/bin/env python3
"""sonde_arc_arma — L'ARC DE TIR EXISTE-T-IL DANS ARMA, OU EST-CE MA FICTION ?

Tout le verdict « le flanc paie » repose sur une regle DURE de mon sandbox : un defenseur
hors de son cone NE PEUT PAS tirer. C'est ce qui cree l'angle mort, et donc la valeur du
contournement.

Sur Arma, rien de tel n'est garanti : un homme qui regarde au nord se retourne peut-etre
des qu'il detecte quelqu'un a l'est. Si c'est le cas, mon arc est une FICTION, et le banc
Arma qui vient de rendre 0 % pour les deux doctrines s'explique tout seul.

LA MESURE — un defenseur oriente au NORD, des attaquants places tout autour :
    0 deg    droit devant lui
    45, 90   sur les cotes
    135, 180 dans son dos
Chacun est seul dans sa cellule, a la meme distance, sur terrain plat. On regarde qui se
fait tirer dessus et qui meurt.

Si le dos est aussi dangereux que le front : PAS D'ARC. Le contournement ne protege de
rien dans le vrai jeu, et il faut le savoir avant d'aller plus loin.
Si le dos est nettement plus sur : l'arc existe, et on peut mesurer sa largeur.

Le defenseur ne PIVOTE pas de lui-meme au depart (disableAI PATH, setDir impose), mais on
NE lui interdit rien d'autre : s'il se retourne, c'est le moteur qui le veut, et c'est
exactement ce qu'on mesure.
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
ANGLES = [0, 45, 90, 135, 180]
DIST = 60.0
ZX, ZY = 23000, 17400
PAS_CELL = 700
DUREE = 90


def _fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main(nom="altis"):
    T = theatre.use(nom)
    b = NativeBridge(port=T.PORT)
    print("=== L'ARC DE TIR EXISTE-T-IL SUR ARMA ? ===", flush=True)
    print("    un defenseur oriente au NORD, un attaquant a %.0f m dans chaque direction" % DIST, flush=True)
    if not b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
        print("  pont MUET")
        _fermer(b)
        return
    print("  pont OK | %d angles | %d s" % (len(ANGLES), DUREE), flush=True)

    c = ["if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; "
         "HMT_S = []; HMT_DEF = []; HMT_ATT = []; HMT_TOUCHE = []; HMT_TIRS = []; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    for i, ang in enumerate(ANGLES):
        K = str(i)
        x = ZX + i * PAS_CELL
        rad = math.radians(ang)
        ax = x + DIST * math.sin(rad)
        ay = ZY + DIST * math.cos(rad)
        c.append(
            "HMT_TOUCHE pushBack 0; HMT_TIRS pushBack 0; "
            "private _gd" + K + " = createGroup east; "
            "private _d" + K + " = _gd" + K + " createUnit [" + Q + "O_Soldier_F" + Q + ", "
            "[" + str(x) + "," + str(ZY) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            "_d" + K + " setPosATL [" + str(x) + "," + str(ZY) + ",0]; "
            "_d" + K + " setDir 0; "                                  # il regarde le NORD
            "_d" + K + " setSkill 0.5; _d" + K + " setUnitPos " + Q + "UP" + Q + "; "
            "_d" + K + " setBehaviour " + Q + "COMBAT" + Q + "; _d" + K + " setCombatMode " + Q + "RED" + Q + "; "
            "_d" + K + " disableAI " + Q + "PATH" + Q + "; "          # il tient sa position
            "_d" + K + " allowDamage false; "                          # on mesure SON tir, pas sa mort
            "_d" + K + " addEventHandler [" + Q + "Fired" + Q + ", { HMT_TIRS set [" + K + ", (HMT_TIRS select " + K + ") + 1] }]; "
            "private _ga" + K + " = createGroup west; "
            "private _a" + K + " = _ga" + K + " createUnit [" + Q + "B_Soldier_F" + Q + ", "
            "[" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            "_a" + K + " setPosATL [" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0]; "
            "_a" + K + " setUnitPos " + Q + "UP" + Q + "; _a" + K + " setBehaviour " + Q + "CARELESS" + Q + "; "
            "_a" + K + " disableAI " + Q + "PATH" + Q + "; _a" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; "
            "_a" + K + " disableAI " + Q + "TARGET" + Q + "; "        # il ne riposte pas : on isole le defenseur
            "_a" + K + " addEventHandler [" + Q + "HandleDamage" + Q + ", { "
            "  if ((_this select 1) == " + Q + Q + ") then { HMT_TOUCHE set [" + K + ", (HMT_TOUCHE select " + K + ") + 1] }; "
            "  _this select 2 }]; "
            "HMT_S pushBack _d" + K + "; HMT_S pushBack _a" + K + "; "
            "HMT_DEF pushBack _d" + K + "; HMT_ATT pushBack _a" + K + "; ")
    c.append("(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_DEF]) call HMT_EMIT;")
    r = b.query("".join(c), r"PRET (\d+)", want=1, timeout=90)
    print("  cellules posees : %s" % (r[-1].group(1) if r else "ECHEC"), flush=True)
    if not r:
        _fermer(b)
        return

    print("", flush=True)
    t = 0
    while t < DUREE:
        time.sleep(15)
        t += 15
        rr = b.query("private _o = " + Q + Q + "; { _o = _o + format [" + Q + P + "1/" + P + "2;" + Q
                     + ", _x, HMT_TOUCHE select _forEachIndex] } forEach HMT_TIRS; "
                     "private _v = " + Q + Q + "; { _v = _v + format [" + Q + P + "1;" + Q
                     + ", if (alive _x) then {1} else {0}] } forEach HMT_ATT; "
                     "(format [" + Q + "R " + P + "1 " + P + "2" + Q + ", _o, _v]) call HMT_EMIT;",
                     r"R (\S+) (\S+)", want=1, timeout=25)
        if rr:
            paires = [p for p in rr[-1].group(1).strip(";").split(";") if "/" in p]
            viv = [v for v in rr[-1].group(2).strip(";").split(";") if v.isdigit()]
            aff = "  ".join("%3d deg: %s tirs %s touches%s"
                            % (ANGLES[i], p.split("/")[0], p.split("/")[1],
                               "" if (i < len(viv) and viv[i] == "1") else " MORT")
                            for i, p in enumerate(paires))
            print("  +%2d s | %s" % (t, aff), flush=True)

    rr = b.query("private _o = " + Q + Q + "; { _o = _o + format [" + Q + P + "1/" + P + "2;" + Q
                 + ", _x, HMT_TOUCHE select _forEachIndex] } forEach HMT_TIRS; "
                 "private _v = " + Q + Q + "; { _v = _v + format [" + Q + P + "1;" + Q
                 + ", if (alive _x) then {1} else {0}] } forEach HMT_ATT; "
                 "(format [" + Q + "R " + P + "1 " + P + "2" + Q + ", _o, _v]) call HMT_EMIT;",
                 r"R (\S+) (\S+)", want=1, timeout=25)
    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S; HMT_S = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    _fermer(b)
    if not rr:
        print("  pas de releve final")
        return

    paires = [p for p in rr[-1].group(1).strip(";").split(";") if "/" in p]
    viv = [v for v in rr[-1].group(2).strip(";").split(";") if v.isdigit()]
    print("", flush=True)
    print("=== RESULTAT ===", flush=True)
    print("  %-10s %10s %10s %10s" % ("angle", "tirs", "touches", "attaquant"), flush=True)
    res = {}
    for i, p in enumerate(paires):
        tirs, tou = (int(x) for x in p.split("/"))
        mort = not (i < len(viv) and viv[i] == "1")
        res[str(ANGLES[i])] = {"tirs": tirs, "touches": tou, "mort": mort}
        print("  %7d deg %10d %10d %10s" % (ANGLES[i], tirs, tou, "MORT" if mort else "vivant"), flush=True)

    devant = res.get("0", {}).get("tirs", 0)
    dos = res.get("180", {}).get("tirs", 0) + res.get("135", {}).get("tirs", 0)
    print("", flush=True)
    print("=== CE QUE CA DECIDE ===", flush=True)
    if devant > 0 and dos == 0:
        print("  L'ARC EXISTE : il tire devant, jamais dans son dos.", flush=True)
        print("  Le contournement protege VRAIMENT. Mon modele est fidele.", flush=True)
    elif dos >= 0.5 * max(devant, 1):
        print("  PAS D'ARC : il tire dans son dos presque autant que devant.", flush=True)
        print("  Mon arc de tir est une FICTION. Le verdict « le flanc paie » repose sur", flush=True)
        print("  un mecanisme que le vrai jeu n'a pas — et ca explique le 0 % des deux", flush=True)
        print("  doctrines sur le banc Arma.", flush=True)
    else:
        print("  ARC PARTIEL : le dos est plus sur, mais pas immunise (%d tirs contre %d)."
              % (dos, devant), flush=True)
        print("  Le contournement aide sans proteger. A quantifier avant d'en faire un verdict.", flush=True)
    json.dump({"distance": DIST, "duree_s": DUREE, "angles": res},
              open(LEV + "/sonde_arc_arma.json", "w"), indent=1)
    print("-> %s/sonde_arc_arma.json" % LEV, flush=True)
    print("SONDEARC_DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "altis")
