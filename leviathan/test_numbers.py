#!/usr/bin/env python3
"""test_numbers.py — TEST A : l'EDGE du NOMBRE. 6 suppresseurs (tir dirige soutenu) vs 2 defenseurs LAMBS.
Chaque defenseur pris par 3 canons concentres. Question : la masse de feu les CLOUE (getSuppression haut)
avant que la base de feu ne fonde ? Spot degage verifie [4000,4000]. Leger, pas de Qwen."""
import sys, time, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

b = NativeBridge(port=5816)
SX, SY = 4000, 4000          # suppresseurs WEST
DX, DY = 4000, 4055          # defenseurs EAST (55 m nord, LOS verifiee)
NSUP, NDEF = 6, 2

SETUP = ('[] spawn { '
    'if (!isNil "HMT_S") then { {deleteVehicle _x} forEach HMT_S }; if (!isNil "HMT_D") then { {deleteVehicle _x} forEach HMT_D }; '
    '{ deleteVehicle _x } forEach (nearestObjects [[%d,%d,0],["Man","Land_BagFence_Long_F","Wall"],350]); '
    'private _gs=createGroup west; HMT_S=[]; for "_i" from 0 to %d do { private _sx=%d+(_i*4)-10; _gs createUnit ["B_soldier_F",[_sx,%d,0],[],0,"NONE"]; private _u=(units _gs) select ((count units _gs)-1); _u setPosATL [_sx,%d,0]; _u setSkill 0.6; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowDamage true; HMT_S pushBack _u; }; '
    'private _gd=createGroup east; HMT_D=[]; for "_i" from 0 to %d do { private _dx=%d+(_i*5); _gd createUnit ["O_Soldier_F",[_dx,%d,0],[],0,"NONE"]; private _u=(units _gd) select ((count units _gd)-1); _u setPosATL [_dx,%d,0]; _u setSkill 0.6; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; HMT_D pushBack _u; }; '
    '{ private _u=_x; { _u reveal [_x,4] } forEach HMT_D } forEach HMT_S; { private _u=_x; { _u reveal [_x,4] } forEach HMT_S } forEach HMT_D; '
    '(format ["HARMATTAN_A ok s=%%1 d=%%2", count HMT_S, count HMT_D]) call HMT_EMIT; };') % (SX, SY, NSUP-1, SX, SY, SY, NDEF-1, DX, DY, DY)

FIRE = '{ private _i=_forEachIndex; if (alive _x) then { private _tg=HMT_D select (_i mod (count HMT_D)); if (!isNull _tg && {alive _tg}) then { _x reveal [_tg,4]; _x doTarget _tg; _x doFire _tg } } } forEach HMT_S; '
MEASURE = ('private _dsup=0; private _da=0; private _dammo=0; { if (alive _x) then { _da=_da+1; _dsup=_dsup max (getSuppression _x); _dammo=_dammo+(_x ammo currentWeapon _x) } } forEach HMT_D; '
    'private _sa=({alive _x} count HMT_S); (format ["HARMATTAN_AS dsup=%1 da=%2 sa=%3 dammo=%4", round(_dsup*100), _da, _sa, _dammo]) call HMT_EMIT;')


def main():
    r = b.query(SETUP, r"HARMATTAN_A ok s=(\d+) d=(\d+)", want=1, timeout=20)
    print("=== TEST A (nombre) : %s suppresseurs vs %s defenseurs, tir dirige concentre ===" % (r[-1].group(1), r[-1].group(2)) if r else "?", flush=True)
    time.sleep(4)
    sup_peak = 0; sa_min = NSUP; dead_def_at = None; dammo0 = None
    for t in range(28):
        rr = b.query(MEASURE, r"HARMATTAN_AS dsup=(-?\d+) da=(\d+) sa=(\d+) dammo=(\d+)", want=1, timeout=15)
        if not rr:
            time.sleep(1.2); continue
        m = rr[-1]; dsup = max(0, int(m.group(1))); da = int(m.group(2)); sa = int(m.group(3)); dammo = int(m.group(4))
        if dammo0 is None: dammo0 = dammo
        sup_peak = max(sup_peak, dsup); sa_min = min(sa_min, sa)
        if da < NDEF and dead_def_at is None: dead_def_at = t
        if t % 2 == 0:
            print("  t=%2d | DEFENSEURS suppr=%3d%% vivants=%d/%d munsTot=%2d | SUPPRESSEURS vivants=%d/%d" % (t, dsup, da, NDEF, dammo, sa, NSUP), flush=True)
        time.sleep(1.2)
    print("=== VERDICT TEST A ===", flush=True)
    print("  suppression MAX des defenseurs : %d%%  (>=50%% = cloue)" % sup_peak, flush=True)
    print("  suppresseurs survivants (min) : %d/%d  (base de feu tient ?)" % (sa_min, NSUP), flush=True)
    print("  defenseurs : premier mort a t=%s" % dead_def_at, flush=True)
    ok = sup_peak >= 50 and sa_min >= NSUP - 2
    print("  >>> LE NOMBRE %s <<<" % ("MARCHE (cloue + tient) — bounding faisable" if ok else "insuffisant"), flush=True)


if __name__ == "__main__":
    main()
