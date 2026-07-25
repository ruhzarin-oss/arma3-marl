#!/usr/bin/env python3
"""test_degel.py — L'IA se bat-elle SANS JOUEUR À PROXIMITÉ ?

Le blocage : Arma gèle les unités loin de tout joueur (dynamic simulation) -> l'IA "sait" mais ne tire pas.
Le correctif : à la création, `enableSimulation true` + `enableDynamicSimulation false` (le « DÉGEL »).

Ce test le prouve : on monte une scène ISOLÉE, LOIN du joueur, avec et sans dégel, et on regarde
si les défenseurs abattent un appât exposé. Si OUI sans joueur -> les bancs tournent en autonomie.

Usage : python test_degel.py --theatre altis [--far 3000] [--wait 20]
"""
import sys, time, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

ap = argparse.ArgumentParser()
ap.add_argument("--far", type=float, default=3000.0, help="distance de la scène par rapport au joueur (m)")
ap.add_argument("--wait", type=int, default=20)
ap.add_argument("--n", type=int, default=6)
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
b = NativeBridge(port=TH.PORT)
fx, fy = TH.FOB


def scene(degel, tx, ty):
    """monte une scène isolée : n défenseurs + 1 appât exposé à 35 m. Renvoie (dmg_appat, def_vivants)."""
    dg = ('_u enableSimulation true; _u enableDynamicSimulation false; ' if degel else '')
    sqf = ('if (!isNil "HMT_TD") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_TD }; HMT_TD=[]; '
           'private _g = createGroup east; '
           'for "_i" from 0 to %d do { '
           '  private _u = _g createUnit ["O_Soldier_F", [%f + (random 20) - 10, %f + (random 20) - 10, 0], [], 0, "NONE"]; '
           '  if (!isNull _u) then { _u setPosATL [getPosATL _u select 0, getPosATL _u select 1, 0]; '
           '    _u setUnitPos "MIDDLE"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setSkill 0.7; %s'
           '    HMT_TD pushBack _u }; }; '
           'HMT_TDB = (createGroup west) createUnit ["B_soldier_F", [%f, %f, 0], [], 0, "NONE"]; '
           'HMT_TDB setPosATL [%f, %f, 0]; HMT_TDB setUnitPos "UP"; HMT_TDB allowDamage true; '
           '%s'
           '{ _x reveal [HMT_TDB, 4] } forEach HMT_TD; '
           '(format ["TD_SET n=%%1", count HMT_TD]) call HMT_EMIT;') % (
               a.n - 1, tx, ty, dg, tx, ty + 35, tx, ty + 35,
               ('HMT_TDB enableSimulation true; HMT_TDB enableDynamicSimulation false; ' if degel else ''))
    r = b.query(sqf, r"TD_SET n=(\d+)", want=1, timeout=25)
    if not r:
        return None
    time.sleep(a.wait)
    q = ('private _d = if (isNull HMT_TDB) then {100} else {round (100 * damage HMT_TDB)}; '
         'private _al = count (HMT_TD select {alive _x}); '
         'private _pd = if (count allPlayers > 0) then {round ((allPlayers select 0) distance HMT_TDB)} else {-1}; '
         '(format ["TD_RES dmg=%1 def=%2 pdist=%3", _d, _al, _pd]) call HMT_EMIT;')
    r2 = b.query(q, r"TD_RES dmg=(\d+) def=(\d+) pdist=(-?\d+)", want=1, timeout=15)
    b.send('if (!isNil "HMT_TD") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_TD }; HMT_TD=[]; '
           'if (!isNil "HMT_TDB" && {!isNull HMT_TDB}) then { deleteVehicle HMT_TDB };')
    return (int(r2[-1].group(1)), int(r2[-1].group(2)), int(r2[-1].group(3))) if r2 else None


print("=== TEST DÉGEL sur %s : l'IA se bat-elle LOIN du joueur ? ===" % TH.WORLD, flush=True)
print("scène montée à %.0f m de l'objectif (donc loin du joueur), attente %d s par bras\n" % (a.far, a.wait), flush=True)
tx, ty = fx + a.far, fy

for label, degel in (("SANS dégel (témoin)", False), ("AVEC dégel      ", True)):
    res = scene(degel, tx, ty)
    if res is None:
        print("  %s : pas de réponse" % label, flush=True); continue
    dmg, alive, pdist = res
    verdict = "IA ACTIVE (elle tire)" if dmg > 5 else "IA INERTE (l'appât est intact)"
    print("  %s : appât abîmé %3d%% | défenseurs %d | joueur à %d m -> %s" % (label, dmg, alive, pdist, verdict), flush=True)

print("\nLECTURE : si 'AVEC dégel' abîme l'appât et pas le témoin -> les bancs tournent SANS toi.", flush=True)
print("TEST_DEGEL_DONE", flush=True)
