import sys
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5801, timeout=20)
POSE = ('private _g = createGroup west; private _u = _g createUnit ["B_Soldier_F", [16000,16000,0], [], 0, "NONE"]; '
        'private _h = createGroup east; private _w = _h createUnit ["O_Soldier_F", [16050,16000,0], [], 0, "NONE"]; sleep 2; ')
NET = ' deleteVehicle _u; deleteVehicle _w; { if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
for nom, expr in [
    ("eyePos/eyePos", '[objNull, "VIEW"] checkVisibility [eyePos _u, eyePos _w]'),
    ("eyePos/AGLtoASL", '[objNull, "VIEW"] checkVisibility [eyePos _u, AGLToASL (aimingPosition _w)]'),
    ("obj=_u",         '[_u, "VIEW"] checkVisibility [eyePos _u, eyePos _w]'),
    ("lineIntersects", '(count (lineIntersectsSurfaces [eyePos _u, eyePos _w, _u, _w])) '),
]:
    sqf = '[] spawn { ' + POSE + 'private _v = ' + expr + '; format ["HMTQ %1", _v] call HMT_EMIT;' + NET
    r = b.query(sqf, r"HMTQ (.*)", want=1, timeout=25)
    print("  %-18s %s" % (nom, (r[0].group(1) if r else "PAS DE REPONSE")))
b.sock.close()
