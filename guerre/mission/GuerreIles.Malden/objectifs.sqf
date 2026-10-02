GUERRE_OBJ = [];
GUERRE_fnc_sol = {
	params ["_o"];
	private _bb = boundingBoxReal _o;
	round (abs (((_bb select 1) select 0) - ((_bb select 0) select 0)) * abs (((_bb select 1) select 1) - ((_bb select 0) select 1)))
};
GUERRE_fnc_objectifs_poser = {
	params ["_liste"];
	{
		_x params ["_k", "_px", "_py", "_sol"];
		private _os = nearestTerrainObjects [[_px, _py], [], 3, true, true];
		private _o = objNull;
		{ if (([_x] call GUERRE_fnc_sol) == _sol) exitWith { _o = _x; }; } forEach _os;
		if (isNull _o && {count _os > 0}) then { _o = _os select 0; };
		private _d = -1;
		private _s = -1;
		if (!isNull _o) then { _d = (getPosASL _o) distance2D [_px, _py]; _s = [_o] call GUERRE_fnc_sol; };
		if (count GUERRE_OBJ <= _k) then { GUERRE_OBJ resize (_k + 1); };
		GUERRE_OBJ set [_k, [_o, 0]];
		["OBJ", [_k, (if (isNull _o) then {0} else {1}), _d, _s]] call LABO_R;
	} forEach _liste;
	["OBJFIN", [count _liste]] call LABO_R;
};
GUERRE_fnc_objectifs_degats = {
	private _n = 0;
	{
		if (!isNil "_x") then {
			_x params ["_o", "_avant"];
			if (!isNull _o) then {
				private _dg = if (alive _o) then {damage _o} else {1};
				if (abs (_dg - _avant) > 0.001) then { _x set [1, _dg]; ["DEG", [_forEachIndex, _dg]] call LABO_R; _n = _n + 1; };
			};
		};
	} forEach GUERRE_OBJ;
	["DEGFIN", [count GUERRE_OBJ, _n]] call LABO_R;
};
