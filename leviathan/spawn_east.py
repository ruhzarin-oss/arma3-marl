#!/usr/bin/env python3
"""spawn_east.py — garnison EAST contrôlée au FOB = la cible de SHAMAL (comme les défenseurs statiques
du sandbox). disableAI PATH -> ils tiennent la position, visent et tirent, mais ne rushent pas."""
import sys, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

ap = argparse.ArgumentParser(); ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--n", type=int, default=14)
a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]
b = NativeBridge(port=5816)
SP = 22 + a.n // 3          # rayon d'etalement qui grandit avec l'effectif (perimetre, pas un tas)
sqf = ('[] spawn { HMT_FOB=[%d,%d]; if (!isNil "HMT_EAST") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_EAST }; HMT_EAST=[]; '
       'private _g = createGroup east; '
       'for "_i" from 0 to %d do { if (_i mod 12 == 0) then { _g = createGroup east }; '
       'private _px=%d+(random %d)-%d; private _py=%d+(random %d)-%d; '
       'private _u = _g createUnit ["O_Soldier_F",[_px,_py,0],[],0,"NONE"]; '
       'if (!isNull _u) then { _u setPosATL [_px,_py,0]; _u setDir (random 360); _u disableAI "PATH"; '
       '_u setUnitPos "MIDDLE"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setSkill 0.5; HMT_EAST pushBack _u }; }; '
       '(format ["HARMATTAN_EAST n=%%1", count HMT_EAST]) call HMT_EMIT; }') % (fx, fy, a.n - 1, fx, 2 * SP, SP, fy, 2 * SP, SP)
r = b.query(sqf, r"HARMATTAN_EAST n=(\d+)", want=1, timeout=25)
print("garnison EAST au FOB [%d,%d] : %s défenseurs (statiques, tiennent+tirent)" % (fx, fy, r[-1].group(1) if r else "?? pas de réponse"))
