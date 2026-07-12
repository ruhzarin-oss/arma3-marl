#!/usr/bin/env python3
"""bounding_ab.py — BOUNDING OVERWATCH en LIVE, A/B suppression ON vs OFF (livrable #5).
Escouade WEST commandee (corps LAMBS ACTIFS, mouvement doMove) vs defenseurs LAMBS EAST :
  - SUPPRESSEURS (overwatch, LOS sur les defenseurs) : ON -> doSuppressiveFire sur le secteur ; OFF -> tiennent le feu.
  - MANOEUVRE : traversent a decouvert vers l'objectif (doMove), exposes aux defenseurs.
Mesure : l'element qui manoeuvre SURVIT-il mieux / traverse-t-il plus loin quand la suppression est ON ?
Leger (pas de Qwen, peu de requetes). Lance 2x : --supp on  puis  --supp off, on compare.
Zone a LOS verifiee (~[5569,4683])."""
import sys, time, ast, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

b = NativeBridge(port=5816)
try:
    INNER = str(ast.literal_eval(open("/home/younes/Bureau/003.ar").read().strip())[0]).replace("'", '"')
except Exception:
    INNER = None

DX, DY = 5569, 4738          # defenseurs EAST
SX, SY = 5569, 4683          # suppresseurs WEST (LOS claire sur D, verifiee)
MX, MY = 5530, 4700          # manoeuvre WEST : depart
OX, OY = 5569, 4712          # objectif : traversee a decouvert devant D
ND, NS, NM = 4, 4, 2


def setup_sqf(supp_on):
    hold = "" if supp_on else 'HMT_S setCombatMode "BLUE"; { _x disableAI "AUTOCOMBAT" } forEach HMT_S; '
    load = ('{ _x setUnitLoadout %s } forEach (HMT_S + HMT_M); ' % INNER) if INNER else ""
    return ('[] spawn { '
        'if (!isNil "HMT_D") then { {deleteVehicle _x} forEach HMT_D }; if (!isNil "HMT_S") then { {deleteVehicle _x} forEach HMT_S }; if (!isNil "HMT_M") then { {deleteVehicle _x} forEach HMT_M }; '
        'for "_i" from 0 to 9 do { deleteMarker ("bd_"+str _i) }; deleteMarker "bd_obj"; '
        'private _gd=createGroup east; HMT_D=[]; for "_i" from 0 to %d do { _gd createUnit ["O_Soldier_F",[%d+(_i*4),%d,0],[],0,"NONE"]; private _u=(units _gd) select ((count units _gd)-1); _u setPosATL [%d+(_i*4),%d,0]; _u setSkill 0.75; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u disableAI "PATH"; HMT_D pushBack _u; }; '
        'private _gs=createGroup west; HMT_S=[]; for "_i" from 0 to %d do { _gs createUnit ["B_soldier_F",[%d+(_i*4),%d,0],[],0,"NONE"]; private _u=(units _gs) select ((count units _gs)-1); _u setPosATL [%d+(_i*4),%d,0]; _u setSkill 0.6; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u disableAI "PATH"; _u setUnitPos "DOWN"; _u forceWalk true; HMT_S pushBack _u; }; '
        'private _gm=createGroup west; HMT_M=[]; for "_i" from 0 to %d do { _gm createUnit ["B_soldier_F",[%d+(_i*4),%d,0],[],0,"NONE"]; private _u=(units _gm) select ((count units _gm)-1); _u setPosATL [%d+(_i*4),%d,0]; _u setSkill 0.6; _u setBehaviour "AWARE"; _u setCombatMode "RED"; HMT_M pushBack _u; }; '
        '%s %s '
        'private _w=_gm addWaypoint [[%d,%d,0],0]; _w setWaypointType "MOVE"; _w setWaypointSpeed "FULL"; _w setWaypointBehaviour "AWARE"; { private _u=_x; { _u reveal [_x,4] } forEach HMT_M } forEach HMT_D; { HMT_S reveal [_x,4] } forEach HMT_D; '
        'createMarker ["bd_obj",[%d,%d,0]]; "bd_obj" setMarkerType "hd_objective"; "bd_obj" setMarkerColor "ColorYellow"; "bd_obj" setMarkerText "OBJ"; '
        'private _dc=[%d,%d]; private _losSD=!(terrainIntersectASL [(getPosASL (HMT_S select 0)) vectorAdd [0,0,1.4],(getPosASL (HMT_D select 0)) vectorAdd [0,0,1.4]]); '
        'private _losDM=!(terrainIntersectASL [(getPosASL (HMT_D select 0)) vectorAdd [0,0,1.4],[%d,%d,(getTerrainHeightASL [%d,%d])+1.4]]); '
        '(format ["HARMATTAN_BD ok d=%%1 s=%%2 m=%%3 losSD=%%4 losDM=%%5", count HMT_D, count HMT_S, count HMT_M, _losSD, _losDM]) call HMT_EMIT; };'
        ) % (ND-1, DX, DY, DX, DY, NS-1, SX, SY, SX, SY, NM-1, MX, MY, MX, MY, load, hold, OX, OY, OX, OY, DX, DY, OX, OY, OX, OY)


STEP_ON = ('{ private _i=_forEachIndex; if (alive _x && {_i < count HMT_D} && {alive (HMT_D select _i)}) then { _x doSuppressiveFire (getPosATL (HMT_D select _i)) } } forEach HMT_S; ')
STEP_MEASURE = ('private _ma=0; private _mind=9999; { if (alive _x) then { _ma=_ma+1; private _d=(getPosATL _x) distance2D [%d,%d]; if (_d<_mind) then {_mind=_d} } } forEach HMT_M; '
    'private _sup=0; private _da=0; { if (alive _x) then { _da=_da+1; _sup=_sup max (getSuppression _x) } } forEach HMT_D; private _sa=({alive _x} count HMT_S); '
    '(format ["HARMATTAN_BDS ma=%%1 mind=%%2 dsup=%%3 da=%%4 sa=%%5", _ma, round _mind, round(_sup*100), _da, _sa]) call HMT_EMIT;') % (OX, OY)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--supp", choices=["on", "off"], required=True); ap.add_argument("--ticks", type=int, default=30)
    a = ap.parse_args(); ON = (a.supp == "on")
    r = b.query(setup_sqf(ON), r"HARMATTAN_BD ok d=(\d+) s=(\d+) m=(\d+) losSD=(\w+) losDM=(\w+)", want=1, timeout=20)
    print("=== BOUNDING A/B [suppression %s] | %s ===" % (a.supp.upper(), r[-1].group(0) if r else "?"), flush=True)
    time.sleep(3)
    last = None
    for t in range(a.ticks):
        sqf = (STEP_ON + STEP_MEASURE) if ON else STEP_MEASURE
        rr = b.query(sqf, r"HARMATTAN_BDS ma=(\d+) mind=(\d+) dsup=(\d+) da=(\d+) sa=(\d+)", want=1, timeout=15)
        if not rr:
            time.sleep(1.3); continue
        m = rr[-1]; d = {"ma": int(m.group(1)), "mind": int(m.group(2)), "dsup": int(m.group(3)), "da": int(m.group(4)), "sa": int(m.group(5))}; last = d
        if t % 3 == 0:
            print("  t=%2d | manoeuvre=%d/%d ->obj=%3dm | suppresseurs=%d/%d | defenseurs=%d/%d supp=%3d%%" % (t, d["ma"], NM, d["mind"], d["sa"], NS, d["da"], ND, d["dsup"]), flush=True)
        if d["ma"] == 0 or d["mind"] < 12:
            break
        time.sleep(1.3)
    print("=== RESULTAT [suppression %s] ===" % a.supp.upper(), flush=True)
    if last:
        res = "OBJECTIF ATTEINT" if last["mind"] < 12 else ("TOUS MORTS" if last["ma"] == 0 else "timeout")
        print("  manoeuvre : %d/%d survivants | dist mini objectif %dm | %s" % (last["ma"], NM, last["mind"], res), flush=True)
        print("  defenseurs : %d/%d vivants | suppression finale %d%%" % (last["da"], ND, last["dsup"]), flush=True)


if __name__ == "__main__":
    main()
