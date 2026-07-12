#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
q = ('private _al = HMT_WPILOT select {alive _x}; if (count _al==0) exitWith { (format ["DG aucune vivante"]) call HMT_EMIT; }; '
     'private _u = _al select 0; private _e = allUnits select {side _x==east && alive _x}; private _ne = if (count _e>0) then {_u findNearestEnemy _u} else {objNull}; '
     '(format ["DG sim=%1 dyn=%2 AT=%3 MOVE=%4 FSM=%5 PATH=%6 ANIM=%7 beh=%8 cm=%9 ammo=%10 ready=%11 tgt=%12 nearEast=%13m", '
     'simulationEnabled _u, dynamicSimulationEnabled _u, _u checkAIFeature "AUTOTARGET", _u checkAIFeature "MOVE", _u checkAIFeature "FSM", _u checkAIFeature "PATH", _u checkAIFeature "ANIM", '
     'behaviour _u, combatMode _u, _u ammo currentWeapon _u, unitReady _u, !(isNull _ne), round (_u distance _ne)]) call HMT_EMIT;')
r = b.query(q, r"DG (.+)", want=1, timeout=15)
print(r[-1].group(1) if r else "pas de reponse")
