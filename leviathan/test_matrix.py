#!/usr/bin/env python3
"""test_matrix.py — POURQUOI les défenseurs ne tirent-ils pas ? On sépare les variables.

Ce matin : défenseurs COUCHÉS + PATH coupé -> n'engagent pas (même joueur à 60 m).
Test dégel  : défenseurs ACCROUPIS -> tuent l'appât à 3 km du joueur.
=> l'hypothèse « l'IA gèle loin du joueur » est FAUSSE. La vraie cause est ailleurs.

Matrice testée (2 répétitions par cellule pour écarter le hasard) :
   posture  : MIDDLE (accroupi)  vs  DOWN (couché, comme le banc)
   dégel    : off                vs  on
Chaque cellule : n défenseurs + appât debout à 35 m, loin du joueur. On mesure les dégâts de l'appât.
"""
import sys, time, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

ap = argparse.ArgumentParser()
ap.add_argument("--far", type=float, default=3000.0)
ap.add_argument("--wait", type=int, default=18)
ap.add_argument("--n", type=int, default=6)
ap.add_argument("--reps", type=int, default=2)
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
b = NativeBridge(port=TH.PORT)
fx, fy = TH.FOB


def cell(posture, degel, nopath, tx, ty):
    dg = ('_u enableSimulation true; _u enableDynamicSimulation false; ' if degel else '')
    np_ = ('_u disableAI "PATH"; ' if nopath else '')
    sqf = ('if (!isNil "HMT_TD") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_TD }; HMT_TD=[]; '
           'if (!isNil "HMT_TDB" && {!isNull HMT_TDB}) then { deleteVehicle HMT_TDB }; '
           'private _g = createGroup east; '
           'for "_i" from 0 to %d do { '
           '  private _u = _g createUnit ["O_Soldier_F", [%f + (random 20) - 10, %f + (random 20) - 10, 0], [], 0, "NONE"]; '
           '  if (!isNull _u) then { _u setPosATL [getPosATL _u select 0, getPosATL _u select 1, 0]; '
           '    _u setUnitPos "%s"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setSkill 0.7; %s%s'
           '    HMT_TD pushBack _u }; }; '
           'HMT_TDB = (createGroup west) createUnit ["B_soldier_F", [%f, %f, 0], [], 0, "NONE"]; '
           'HMT_TDB setPosATL [%f, %f, 0]; HMT_TDB setUnitPos "UP"; HMT_TDB allowDamage true; '
           '{ _x reveal [HMT_TDB, 4] } forEach HMT_TD; '
           '(format ["C_SET n=%%1", count HMT_TD]) call HMT_EMIT;') % (
               a.n - 1, tx, ty, posture, np_, dg, tx, ty + 35, tx, ty + 35)
    if not b.query(sqf, r"C_SET n=(\d+)", want=1, timeout=25):
        return None
    time.sleep(a.wait)
    q = ('private _d = if (isNull HMT_TDB) then {100} else {round (100 * damage HMT_TDB)}; '
         'private _kn = 0; { private _k = _x knowsAbout HMT_TDB; if (_k > _kn) then {_kn = _k} } forEach (HMT_TD select {alive _x}); '
         '(format ["C_RES dmg=%1 known=%2", _d, round (10 * _kn)]) call HMT_EMIT;')
    r = b.query(q, r"C_RES dmg=(\d+) known=(\d+)", want=1, timeout=15)
    b.send('if (!isNil "HMT_TD") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_TD }; HMT_TD=[]; '
           'if (!isNil "HMT_TDB" && {!isNull HMT_TDB}) then { deleteVehicle HMT_TDB };')
    return (int(r[-1].group(1)), int(r[-1].group(2)) / 10.0) if r else None


print("=== MATRICE : pourquoi les défenseurs n'engagent-ils pas ? (%s, loin du joueur) ===" % TH.WORLD, flush=True)
print("%-28s %10s %10s" % ("configuration", "appât %", "détecté"), flush=True)
tx, ty = fx + a.far, fy
CASES = [
    ("accroupi, PATH libre", "MIDDLE", False, False),
    ("accroupi + dégel", "MIDDLE", True, False),
    ("COUCHÉ, PATH libre", "DOWN", False, False),
    ("COUCHÉ + PATH coupé (banc)", "DOWN", False, True),
]
for label, posture, degel, nopath in CASES:
    dmgs, kns = [], []
    for _ in range(a.reps):
        res = cell(posture, degel, nopath, tx, ty)
        if res:
            dmgs.append(res[0]); kns.append(res[1])
    if dmgs:
        print("%-28s %9.0f%% %10.1f" % (label, sum(dmgs) / len(dmgs), sum(kns) / len(kns)), flush=True)
    else:
        print("%-28s %10s %10s" % (label, "?", "?"), flush=True)

print("\nLECTURE : appât ~100%% = les défenseurs engagent. 'détecté' proche de 4 = ils SAVENT (donc si dmg=0, ils voient mais ne tirent pas).", flush=True)
print("MATRIX_DONE", flush=True)
