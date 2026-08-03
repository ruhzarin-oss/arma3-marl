#!/usr/bin/env python3
"""sonde_gel — LES UNITES SONT-ELLES GELEES PAR LA SIMULATION DYNAMIQUE ?

Symptome : dans la sonde d'arc, les compteurs (tirs, impacts) avancent pendant ~20 s puis
NE BOUGENT PLUS DU TOUT, sur les cinq cellules a la fois. Ce n'est pas un comportement
tactique : c'est un arret de simulation.

Suspect : ALiVE active la SIMULATION DYNAMIQUE. Une unite loin de tout joueur est
desactivee au bout de quelques secondes. `envelop_arma.py` le contourne deja, avec un
commentaire explicite : « DEGEL : simule meme sans joueur proche (sinon l'escouade reste
inerte) » -> `_u enableSimulation true; _u enableDynamicSimulation false;`.
Aucune de mes sondes ne le fait. La sonde de suppression du 27/07 non plus — et elle a
rendu ZERO balle dans les deux bras.

L'EPREUVE : deux paires identiques, cote a cote, meme cellule, MEME instant.
    GELEE  : creee comme aujourd'hui
    DEGELEE: + enableSimulation true + enableDynamicSimulation false
On compte les tirs sur 60 s. Si la degelee tire et la gelee non, tout ce qui precede
s'explique et se repare en deux lignes.
"""
import sys
import time
import json

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"
CELLS = json.load(open(LEV + "/cellules_altis.json"))["serie"]
DUREE = 60


def paire(K, cx, cy, degel):
    d = ("_d setPosATL [" + str(cx) + "," + str(cy) + ",0]; _d setDir 0; _d setSkill 0.5; "
         "_d setUnitPos " + Q + "UP" + Q + "; _d setBehaviour " + Q + "COMBAT" + Q + "; "
         "_d setCombatMode " + Q + "RED" + Q + "; _d disableAI " + Q + "PATH" + Q + "; "
         "_d addEventHandler [" + Q + "HandleDamage" + Q + ", { ((_this select 2) min 0.55) }]; ")
    at = ("_at setPosATL [" + str(cx) + "," + str(cy + 60) + ",0]; _at setDir 180; _at setSkill 0.6; "
          "_at setUnitPos " + Q + "UP" + Q + "; _at setBehaviour " + Q + "COMBAT" + Q + "; "
          "_at setCombatMode " + Q + "RED" + Q + "; _at disableAI " + Q + "PATH" + Q + "; "
          "_at addEventHandler [" + Q + "HandleDamage" + Q + ", { 0 }]; ")
    deg = ("_d enableSimulation true; _d enableDynamicSimulation false; "
           "_at enableSimulation true; _at enableDynamicSimulation false; ") if degel else ""
    return ("HMT_N pushBack 0; "
            "private _gd = createGroup east; private _ga = createGroup west; "
            "private _d = _gd createUnit [" + Q + "O_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            "private _at = _ga createUnit [" + Q + "B_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy + 60) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            + d + at + deg +
            "_d setVariable [" + Q + "hmt_k" + Q + ", " + str(K) + "]; "
            "_at setVariable [" + Q + "hmt_k" + Q + ", " + str(K) + "]; "
            "_d addEventHandler [" + Q + "Fired" + Q + ", { private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
            "  if (_k >= 0) then { HMT_N set [_k, (HMT_N select _k) + 1] }; }]; "
            "_at addEventHandler [" + Q + "Fired" + Q + ", { private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
            "  if (_k >= 0) then { HMT_N set [_k, (HMT_N select _k) + 1] }; }]; "
            "_at reveal [_d, 4]; _d reveal [_at, 4]; "
            "HMT_S pushBack _d; HMT_S pushBack _at; HMT_U pushBack _d; HMT_A pushBack _at; ")


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    try:
        r = b.query("(format [" + Q + "SYS " + P + "1 " + P + "2" + Q + ", "
                    "(if (dynamicSimulationSystemEnabled) then {1} else {0}), count allUnits]) call HMT_EMIT;",
                    r"SYS (\d+) (\d+)", want=1, timeout=25)
        if not r:
            print("pont MUET")
            return 2
        print("simulation dynamique du systeme : %s | unites presentes : %s"
              % ("ACTIVE" if r[-1].group(1) == "1" else "inactive", r[-1].group(2)), flush=True)

        c = ["if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; "
             "HMT_S = []; HMT_U = []; HMT_A = []; HMT_N = []; "
             "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
        # 0 = GELEE (comme aujourd hui), 1 = DEGELEE
        c.append(paire(0, CELLS[0][0], CELLS[0][1], False))
        c.append(paire(1, CELLS[1][0], CELLS[1][1], True))
        c.append(paire(2, CELLS[2][0], CELLS[2][1], False))
        c.append(paire(3, CELLS[3][0], CELLS[3][1], True))
        c.append("(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_U]) call HMT_EMIT;")
        r = b.query("".join(c), r"PRET (\d+)", want=1, timeout=90)
        print("paires posees : %s  (0 et 2 GELEES, 1 et 3 DEGELEES)" % (r[-1].group(1) if r else "ECHEC"), flush=True)
        if not r:
            return 2

        for t in range(0, DUREE + 1, 10):
            if t:
                time.sleep(10)
            b.send("{ private _k = _forEachIndex; private _d = HMT_U select _k; "
                   "  if (alive _x && alive _d) then { _x reveal [_d, 4]; _x doTarget _d; _x doFire _d; }; "
                   "} forEach HMT_A;", wait=False)
            q = ("private _o = " + Q + Q + "; { private _k = _forEachIndex; "
                 " _o = _o + format [" + Q + P + "1/" + P + "2/" + P + "3;" + Q + ", HMT_N select _k, "
                 "  (if (simulationEnabled _x) then {1} else {0}), "
                 "  (if (dynamicSimulationEnabled _x) then {1} else {0})]; } forEach HMT_U; "
                 "(format [" + Q + "G " + P + "1" + Q + ", _o]) call HMT_EMIT;")
            rr = b.query(q, r"G (\S+)", want=1, timeout=25)
            if rr:
                cells = [p for p in rr[-1].group(1).strip(";").split(";") if "/" in p]
                print("  +%2ds  " % t + "   ".join(
                    "%s %s tirs=%s sim=%s dyn=%s" % (i, "GEL " if i in (0, 2) else "DEGEL",
                                                     p.split("/")[0], p.split("/")[1], p.split("/")[2])
                    for i, p in enumerate(cells)), flush=True)
        b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S; HMT_S = []; "
               "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    finally:
        try:
            b.close()
        except Exception:
            pass
    print("GEL_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
