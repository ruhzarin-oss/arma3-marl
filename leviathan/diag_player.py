#!/usr/bin/env python3
"""diag_player.py — pourquoi le joueur WEST se fait tirer par ses propres agents ?"""
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('private _pl=(allUnits select {isPlayer _x}) param [0,objNull]; '
       'if (isNull _pl) then { "DIAG no_player" call HMT_EMIT; } else { '
       'private _wk=({alive _x && _x knowsAbout _pl>1.4} count HMT_WPILOT); '
       'private _wtgt=({alive _x && (currentTarget _x)==_pl} count HMT_WPILOT); '
       'private _near=({alive _x && _x distance _pl<40} count HMT_WPILOT); '
       '(format ["DIAG side=%1 alive=%2 rating=%3 captive=%4 WESTknows=%5 WESTtarget=%6 WESTnear40m=%7", '
       'str side _pl, alive _pl, round rating _pl, captive _pl, _wk, _wtgt, _near]) call HMT_EMIT; };')
r = b.query(sqf, r"DIAG (.+)", want=1, timeout=12)
print("RESULT:", r[-1].group(1) if r else "pas de reponse")
