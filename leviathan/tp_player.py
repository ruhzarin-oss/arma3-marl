#!/usr/bin/env python3
"""tp_player.py — teleporte le joueur au centre des WEST (SHAMAL) pour inspecter de pres, et re-applique captive+invuln."""
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('private _w = HMT_WPILOT select {alive _x}; '
       'if (count _w > 0) then { '
       'private _cx=0; private _cy=0; { _cx=_cx+(getPosATL _x)#0; _cy=_cy+(getPosATL _x)#1 } forEach _w; '
       '_cx=_cx/(count _w); _cy=_cy/(count _w); '
       '{ _x setPosATL [_cx, _cy+8, 0]; _x setCaptive true; _x allowDamage false } forEach (allUnits select {isPlayer _x}); '
       '(format ["TP ok centre=[%1,%2] west=%3", round _cx, round _cy, count _w]) call HMT_EMIT; '
       '} else { "TP no_west_alive" call HMT_EMIT; };')
r = b.query(sqf, r"TP (.+)", want=1, timeout=12)
print("RESULT:", r[-1].group(1) if r else "pas de reponse")
