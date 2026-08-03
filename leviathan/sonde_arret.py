#!/usr/bin/env python3
"""sonde_arret — POURQUOI LE TIR S'ARRETE-T-IL A 20 SECONDES ?

Fait mesure : sur quatre cellules independantes, les compteurs de tir montent pendant
10-20 s puis ne bougent plus, definitivement. La simulation dynamique est innocente
(`simulationEnabled` = 1, `dynamicSimulationEnabled` = 0 partout, et les paires « degelees »
s'arretent exactement comme les autres).

Deux familles d'explications, et il faut les separer AVANT d'interpreter quoi que ce soit :
  (I)  l'IA a vraiment cesse de tirer  -> munitions, cible perdue, blessure, comportement
  (II) c'est le COMPTEUR qui est mort  -> le gestionnaire Fired ne se declenche plus

On les separe avec une deuxieme mesure independante du compteur : les MUNITIONS RESTANTES.
Si les munitions descendent alors que le compteur est fige, c'est (II) : instrument casse.
Si les munitions ne bougent plus non plus, c'est (I) : comportement.

Quatre cellules, quatre regimes de degats — la seule chose qui change :
  0  aucun gestionnaire de degats           (les deux mortels)
  1  defenseur allowDamage false            (attaquant mortel)
  2  HandleDamage des deux cotes            (le montage de la sonde d'arc)
  3  comme 2, plus REARMEMENT toutes les 10 s (setVehicleAmmo 1)
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
DUREE = 90


def cellule(K, cx, cy, regime):
    base = (
        "HMT_ND pushBack 0; HMT_NA pushBack 0; "
        "private _gd = createGroup east; private _ga = createGroup west; "
        "private _d = _gd createUnit [" + Q + "O_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
        "private _at = _ga createUnit [" + Q + "B_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy + 60) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
        "_d setPosATL [" + str(cx) + "," + str(cy) + ",0]; _d setDir 0; _d setSkill 0.5; "
        "_at setPosATL [" + str(cx) + "," + str(cy + 60) + ",0]; _at setDir 180; _at setSkill 0.6; "
        "{ _x setUnitPos " + Q + "UP" + Q + "; _x setBehaviour " + Q + "COMBAT" + Q + "; "
        "  _x setCombatMode " + Q + "RED" + Q + "; _x disableAI " + Q + "PATH" + Q + "; "
        "  _x enableSimulation true; _x enableDynamicSimulation false; } forEach [_d, _at]; "
        "_d setVariable [" + Q + "hmt_k" + Q + ", " + str(K) + "]; "
        "_at setVariable [" + Q + "hmt_k" + Q + ", " + str(K) + "]; "
        "_d addEventHandler [" + Q + "Fired" + Q + ", { private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
        "  if (_k >= 0) then { HMT_ND set [_k, (HMT_ND select _k) + 1] }; }]; "
        "_at addEventHandler [" + Q + "Fired" + Q + ", { private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
        "  if (_k >= 0) then { HMT_NA set [_k, (HMT_NA select _k) + 1] }; }]; "
        "_at reveal [_d, 4]; _d reveal [_at, 4]; ")
    if regime == 0:
        deg = ""
    elif regime == 1:
        deg = "_d allowDamage false; "
    else:
        deg = ("_d addEventHandler [" + Q + "HandleDamage" + Q + ", { ((_this select 2) min 0.55) }]; "
               "_at addEventHandler [" + Q + "HandleDamage" + Q + ", { 0 }]; ")
    return base + deg + "HMT_S pushBack _d; HMT_S pushBack _at; HMT_D pushBack _d; HMT_A pushBack _at; "


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    try:
        c = ["if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; "
             "HMT_S = []; HMT_D = []; HMT_A = []; HMT_ND = []; HMT_NA = []; "
             "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
        for k in range(4):
            c.append(cellule(k, CELLS[k][0], CELLS[k][1], k))
        c.append("(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_D]) call HMT_EMIT;")
        r = b.query("".join(c), r"PRET (\d+)", want=1, timeout=90)
        print("cellules : %s  (0 mortels | 1 def invuln | 2 HandleDamage | 3 HandleDamage+rearme)"
              % (r[-1].group(1) if r else "ECHEC"), flush=True)
        if not r:
            return 2
        print("  regime  tirsD tirsA  balles_chargeurD  balles_chargeurA  vivD vivA  saitD", flush=True)
        for t in range(0, DUREE + 1, 10):
            if t:
                time.sleep(10)
            b.send("{ private _k = _forEachIndex; private _d = HMT_D select _k; "
                   "  if (alive _x && alive _d) then { _x reveal [_d, 4]; _x doTarget _d; _x doFire _d; "
                   "    _d reveal [_x, 4]; _d doTarget _x; }; } forEach HMT_A; "
                   "private _r3 = HMT_A select 3; private _s3 = HMT_D select 3; "
                   "if (alive _r3) then { _r3 setVehicleAmmo 1 }; if (alive _s3) then { _s3 setVehicleAmmo 1 };",
                   wait=False)
            q = ("private _o = " + Q + Q + "; { private _k = _forEachIndex; private _at = HMT_A select _k; "
                 " _o = _o + format [" + Q + P + "1/" + P + "2/" + P + "3/" + P + "4/" + P + "5/" + P + "6/" + P + "7;" + Q + ", "
                 "  HMT_ND select _k, HMT_NA select _k, "
                 "  (_x ammo (primaryWeapon _x)) + 30 * (count (magazines _x)), "
                 "  (_at ammo (primaryWeapon _at)) + 30 * (count (magazines _at)), "
                 "  (if (alive _x) then {1} else {0}), (if (alive _at) then {1} else {0}), "
                 "  round (10 * (_x knowsAbout _at))]; } forEach HMT_D; "
                 "(format [" + Q + "A " + P + "1" + Q + ", _o]) call HMT_EMIT;")
            rr = b.query(q, r"A (\S+)", want=1, timeout=25)
            if rr:
                cells = [p for p in rr[-1].group(1).strip(";").split(";") if "/" in p]
                print("  +%2ds" % t, flush=True)
                for i, p in enumerate(cells):
                    v = p.split("/")
                    print("     %d      %5s %5s   %14s   %15s   %3s %3s  %4.1f"
                          % (i, v[0], v[1], v[2], v[3], v[4], v[5], int(v[6]) / 10.0), flush=True)
        b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S; HMT_S = []; "
               "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    finally:
        try:
            b.close()
        except Exception:
            pass
    print("ARRET_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
