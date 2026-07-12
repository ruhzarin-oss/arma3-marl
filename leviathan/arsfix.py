import sys; sys.path.insert(0,"/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b=NativeBridge(port=5816)
sqf=("[] spawn { private _ok = !isNil \"ace_arsenal_fnc_initBox\"; private _boxes=[]; "
 "if (!isNil \"HMT_CAS_ARSENAL\" && {!isNull HMT_CAS_ARSENAL}) then { _boxes pushBack HMT_CAS_ARSENAL; }; "
 "private _nb=\"Box_NATO_Equip_F\" createVehicle [2300,2007,0]; _nb setPosATL [2300,2007,0]; _nb allowDamage false; _boxes pushBack _nb; HMT_CAS_ARSENAL=_nb; "
 "{ if (_ok) then { [_x,true] call ace_arsenal_fnc_initBox; }; [\"AmmoboxInit\",[_x,true]] call BIS_fnc_arsenal; } forEach _boxes; "
 "deleteMarker \"HMT_ARSENAL_MK\"; createMarker [\"HMT_ARSENAL_MK\",[2300,2010,0]]; \"HMT_ARSENAL_MK\" setMarkerType \"loc_Ammo\"; \"HMT_ARSENAL_MK\" setMarkerColor \"ColorWEST\"; \"HMT_ARSENAL_MK\" setMarkerText \"ARSENAL ACE\"; "
 "(format [\"HARMATTAN_ARSFIX ace_fn=%1 nboxes=%2 pos=%3\", _ok, count _boxes, getPosATL _nb]) call HMT_EMIT; };")
r=b.query(sqf, r"HARMATTAN_ARSFIX ace_fn=(\w+) nboxes=(\d+) pos=(\[.*\])", want=1, timeout=15)
print("ARSFIX:", r[-1].group(0)) if r else print("pas de reponse")
