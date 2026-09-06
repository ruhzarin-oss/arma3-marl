import sys
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5801, timeout=20)
for nom, sqf in [
    ("direct",      'format ["HMTP1 %1", 6*7] call HMT_EMIT;'),
    ("spawn",       '[] spawn { sleep 1; format ["HMTP2 %1", 6*7] call HMT_EMIT; };'),
    ("randomPos",   '[] spawn { private _p = [] call BIS_fnc_randomPos; format ["HMTP3 %1 %2", _p select 0, _p select 1] call HMT_EMIT; };'),
    ("createUnit",  '[] spawn { private _g = createGroup west; private _u = _g createUnit ["B_Soldier_F", [16000,16000,0], [], 0, "NONE"]; sleep 2; format ["HMTP4 %1 %2", count units _g, alive _u] call HMT_EMIT; deleteVehicle _u; { if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'),
    ("checkVis",    '[] spawn { private _g = createGroup west; private _u = _g createUnit ["B_Soldier_F", [16000,16000,0], [], 0, "NONE"]; private _h = createGroup east; private _w = _h createUnit ["O_Soldier_F", [16050,16000,0], [], 0, "NONE"]; sleep 2; private _v = [objNull, "VIEW"] checkVisibility [eyePos _u, aimingPosition _w]; format ["HMTP5 %1 %2 %3", _v, getPosATL _u select 2, alive _w] call HMT_EMIT; deleteVehicle _u; deleteVehicle _w; { if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'),
]:
    r = b.query(sqf, r"HMTP\d (.*)", want=1, timeout=25)
    print("  %-11s %s" % (nom, (r[0].group(0) if r else "PAS DE REPONSE")))
b.sock.close()
