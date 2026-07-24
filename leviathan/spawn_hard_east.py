#!/usr/bin/env python3
"""spawn_hard_east.py — défense DURCIE au FOB (la position "imprenable" de l'A/B).
LAMBS ACTIF (on ne coupe PAS la FSM danger -> suppression/réactions), skill 0.9, COUCHÉS (petite cible),
1 mitrailleur sur 3, périmètre SERRÉ (appui mutuel). disableAI PATH -> ils tiennent, ne rushent pas.
Objectif : que l'ASSAUT FRONTAL casse dessus, et que seul le DÉBORDEMENT passe."""
import sys, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

ap = argparse.ArgumentParser(); ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--n", type=int, default=12)
ap.add_argument("--skill", type=float, default=0.9)
a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]
b = NativeBridge(port=5816)
SP = 16 + a.n // 4          # périmètre serré (appui mutuel, feux croisés)
sqf = ('[] spawn { HMT_FOB=[%d,%d]; if (!isNil "HMT_EAST") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_EAST }; HMT_EAST=[]; '
       'private _g = createGroup east; '
       'for "_i" from 0 to %d do { if (_i mod 8 == 0) then { _g = createGroup east }; '
       'private _cls = if (_i mod 3 == 0) then { "O_Soldier_AR_F" } else { "O_Soldier_F" }; '   # 1 mitrailleur / 3
       'private _px=%d+(random %d)-%d; private _py=%d+(random %d)-%d; '
       'private _u = _g createUnit [_cls,[_px,_py,0],[],0,"NONE"]; '
       'if (!isNull _u) then { _u setPosATL [_px,_py,0]; _u setDir (random 360); '
       '_u disableAI "PATH"; _u setUnitPos "DOWN"; '                                              # tiennent + couchés
       '_u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setSkill %.2f; '                     # LAMBS reste actif (pas de disableAI FSM)
       'HMT_EAST pushBack _u }; }; '
       '(format ["HARMATTAN_EAST n=%%1", count HMT_EAST]) call HMT_EMIT; }') % (
           fx, fy, a.n - 1, fx, 2 * SP, SP, fy, 2 * SP, SP, a.skill)
r = b.query(sqf, r"HARMATTAN_EAST n=(\d+)", want=1, timeout=25)
print("défense DURCIE au FOB [%d,%d] : %s défenseurs (LAMBS actif, skill %.2f, couchés, 1 MG/3, périmètre %dm)" % (
    fx, fy, r[-1].group(1) if r else "??", a.skill, SP))
