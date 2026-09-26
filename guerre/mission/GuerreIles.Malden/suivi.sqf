if (isNil "GUERRE_reserve") then { GUERRE_reserve = [[], []]; };
if (isNil "GUERRE_morts_ids") then { GUERRE_morts_ids = []; };

GUERRE_fnc_prendre = {
	params ["_i", "_n"];
	private _r = GUERRE_reserve select _i;
	private _pris = _r select [0, _n];
	GUERRE_reserve set [_i, _r select [_n, count _r]];
	_pris
};

GUERRE_fnc_numeroter = {
	params ["_i", "_u", "_k"];
	_u setVariable ["GUERRE_id", _k];
	_u setVariable ["GUERRE_camp", _i];
};

GUERRE_fnc_poser_escouade = {
	params ["_i", "_base"];
	private _cls = GUERRE_ESCOUADE select _i;
	if ((count (GUERRE_reserve select _i)) < (count _cls)) exitWith {
		GUERRE_caisse set [_i, (GUERRE_caisse select _i) + (GUERRE_COUT_ESCOUADE select _i)];
		GUERRE_depense set [_i, (GUERRE_depense select _i) - (GUERRE_COUT_ESCOUADE select _i)];
		GUERRE_achats set [_i, (GUERRE_achats select _i) - 1];
		GUERRE_sans_soldats = (missionNamespace getVariable ["GUERRE_sans_soldats", 0]) + 1;
		grpNull
	};
	private _ids = [_i, count _cls] call GUERRE_fnc_prendre;
	private _p = [_base] call GUERRE_fnc_lieu;
	private _g = createGroup [GUERRE_CAMPS select _i, true];
	{
		private _u = _g createUnit [_x, _p, [], 8, "FORM"];
		[_i, _u, _ids select _forEachIndex] call GUERRE_fnc_numeroter;
		_u allowFleeing 0;
	} forEach _cls;
	_g setVariable ["GUERRE_camp", _i];
	(GUERRE_groupes select _i) pushBack _g;
	_g
};

GUERRE_fnc_poser_vehicule = {
	params ["_i", "_base"];
	if ((count (GUERRE_reserve select _i)) < 3) exitWith {
		GUERRE_caisse set [_i, (GUERRE_caisse select _i) + (GUERRE_COUT_VEHICULE select _i)];
		GUERRE_depense set [_i, (GUERRE_depense select _i) - (GUERRE_COUT_VEHICULE select _i)];
		grpNull
	};
	private _p = [_base] call GUERRE_fnc_lieu;
	private _v = createVehicle [GUERRE_VEHICULE select _i, _p, [], 0, "NONE"];
	createVehicleCrew _v;
	private _g = group (effectiveCommander _v);
	private _ids = [_i, count (units _g)] call GUERRE_fnc_prendre;
	{ [_i, _x, _ids select _forEachIndex] call GUERRE_fnc_numeroter; _x allowFleeing 0; } forEach (units _g);
	_g setVariable ["GUERRE_camp", _i];
	(GUERRE_groupes select _i) pushBack _g;
	_g
};

if (isNil "GUERRE_EH_SUIVI") then {
	GUERRE_EH_SUIVI = addMissionEventHandler ["EntityKilled", {
		params ["_mort"];
		private _k = _mort getVariable ["GUERRE_id", -1];
		if (_k > 0) then { GUERRE_morts_ids pushBack [_mort getVariable ["GUERRE_camp", -1], _k]; };
	}];
};

GUERRE_fnc_tour2 = {
	params ["_pe", "_pw", "_re", "_rw"];
	GUERRE_reserve set [0, (GUERRE_reserve select 0) + _re];
	GUERRE_reserve set [1, (GUERRE_reserve select 1) + _rw];
	[_pe, _pw] call GUERRE_fnc_tour;
	["RESERVE", [count (GUERRE_reserve select 0), count (GUERRE_reserve select 1), missionNamespace getVariable ["GUERRE_sans_soldats", 0]]] call LABO_R;
};

GUERRE_fnc_marquer = {
	params ["_i", "_k", "_p", "_vivant"];
	private _m = format ["g_%1_%2", _i, _k];
	if (_vivant) then {
		if ((markerType _m) isEqualTo "") then { createMarker [_m, _p]; _m setMarkerShape "ICON"; _m setMarkerSize [0.5, 0.5]; _m setMarkerType "mil_dot"; _m setMarkerColor (["ColorOPFOR", "ColorBLUFOR"] select _i); } else { _m setMarkerPos _p; };
	} else {
		if !((markerType _m) isEqualTo "") then { _m setMarkerType "mil_destroy"; _m setMarkerColor "ColorBlack"; };
	};
};

GUERRE_fnc_positions = {
	{
		private _i = _x;
		{
			{
				private _k = _x getVariable ["GUERRE_id", -1];
				if ((_k > 0) && { alive _x }) then {
					private _p = getPosATL _x;
					["U", [_i, _k, round (_p select 0), round (_p select 1), (round ((damage _x) * 100)) / 100]] call LABO_R;
					[_i, _k, _p, true] call GUERRE_fnc_marquer;
				};
			} forEach (units _x);
		} forEach (GUERRE_groupes select _i);
	} forEach [0, 1];
	private _m = GUERRE_morts_ids;
	GUERRE_morts_ids = [];
	{ ["MORT", _x] call LABO_R; [_x select 0, _x select 1, [0, 0, 0], false] call GUERRE_fnc_marquer; } forEach _m;
};

GUERRE_fnc_identifier = {
	params ["_re", "_rw"];
	{
		private _i = _forEachIndex;
		private _ids = _x;
		private _n = 0;
		private _sans = 0;
		{
			{
				if ((alive _x) && { (_x getVariable ["GUERRE_id", -1]) < 0 }) then {
					if (_n < (count _ids)) then { [_i, _x, _ids select _n] call GUERRE_fnc_numeroter; _n = _n + 1; } else { _sans = _sans + 1; };
				};
			} forEach (units _x);
		} forEach (GUERRE_groupes select _i);
		GUERRE_reserve set [_i, (GUERRE_reserve select _i) + (_ids select [_n, count _ids])];
		["IDENTIFIE", [_i, _n, _sans]] call LABO_R;
	} forEach [_re, _rw];
};

if (isNil "GUERRE_JOUEURS") then {
	GUERRE_JOUEURS = [] spawn {
		while { true } do {
			{
				private _m = format ["j_%1", getPlayerUID _x];
				if ((markerType _m) isEqualTo "") then { createMarker [_m, getPosATL _x]; _m setMarkerShape "ICON"; _m setMarkerType "mil_dot"; _m setMarkerColor "ColorYellow"; _m setMarkerSize [0.9, 0.9]; } else { _m setMarkerPos (getPosATL _x); };
			} forEach (allPlayers select { !(_x isKindOf "HeadlessClient_F") });
			sleep 1;
		};
	};
};
