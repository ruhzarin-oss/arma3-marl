if (isNil "GUERRE_PLAFOND_HOMMES") then { GUERRE_PLAFOND_HOMMES = 100; };
if (isNil "GUERRE_annules") then { GUERRE_annules = [0, 0]; };
GUERRE_PLAFOND_CAISSE = 3;
GUERRE_RATIO_ASSAUT = 3;
GUERRE_DIST_RALLIEMENT = 800;
GUERRE_MIN_DEFENSEURS = 8;

GUERRE_fnc_hommes = { params ["_g"]; { alive _x } count (units _g) };

GUERRE_fnc_ennemis_connus = {
	params ["_i", "_pos", "_rayon"];
	private _cote = GUERRE_CAMPS select _i;
	private _adv = [GUERRE_CAMPS select (1 - _i), independent];
	{ (alive _x) && { (side group _x) in _adv } && { (_x distance2D _pos) < _rayon } && { (_cote knowsAbout _x) > 1 } } count allUnits
};

GUERRE_fnc_ralliement = {
	params ["_i", "_cible", "_base"];
	private _cle = format ["GUERRE_rp_%1", _i];
	private _rp = _cible getVariable [_cle, []];
	if ((count _rp) == 0) then {
		private _pc = getPos _cible;
		private _pb = getPos _base;
		private _d = (_pc distance2D _pb) max 1;
		private _f = (GUERRE_DIST_RALLIEMENT min (_d * 0.8)) / _d;
		private _p = [(_pc select 0) + ((_pb select 0) - (_pc select 0)) * _f, (_pc select 1) + ((_pb select 1) - (_pc select 1)) * _f, 0];
		_rp = [_p, 0, 150, 5, 0, 0.4, 0] call BIS_fnc_findSafePos;
		if (((count _rp) < 2) || { (_rp distance2D _p) > 200 }) then { _rp = _p; };
		_rp = [_rp select 0, _rp select 1, 0];
		_cible setVariable [_cle, _rp];
	};
	_rp
};

GUERRE_fnc_choisir_cible = {
	params ["_i"];
	private _cote = [east, west] select _i;
	private _liste = [_cote] call BIS_fnc_WLSectorListing;
	private _dispo = _liste select 1;
	private _tenus = (_liste select 2) select { !isNull _x };
	if ((count _dispo) == 0) exitWith { objNull };
	private _baseEnnemie = [1 - _i] call GUERRE_fnc_base;
	private _forces = [_i] call GUERRE_fnc_vivants;
	private _meilleur = objNull;
	private _note = -1;
	{
		private _s = _x;
		private _ps = getPos (_s getVariable ["BIS_WL_sectorZR", _s]);
		private _def = [_i, _ps, 400] call GUERRE_fnc_ennemis_connus;
		private _d = 1e9;
		{ _d = _d min ((getPos _x) distance2D _ps); } forEach _tenus;
		private _n = (_s getVariable ["BIS_WL_value", 10]) / ((1 + _def) * (1 + (_d / 1000)));
		if (_s isEqualTo _baseEnnemie) then { _n = if (_forces >= (GUERRE_RATIO_ASSAUT * (GUERRE_MIN_DEFENSEURS max _def))) then { 1e6 } else { -1 }; };
		if (_n > _note) then { _note = _n; _meilleur = _s; };
	} forEach _dispo;
	_meilleur
};

GUERRE_fnc_voter = {
	params ["_i"];
	if (!isNull ([_i] call GUERRE_fnc_cible)) exitWith {};
	private _c = [_i] call GUERRE_fnc_choisir_cible;
	if (isNull _c) exitWith {};
	private _cote = [east, west] select _i;
	private _n = 0;
	{ if ((!isPlayer _x) && { alive _x } && { (side group _x) isEqualTo _cote }) then { _x setVariable ["BIS_WL_selectedSector", _c, true]; _n = _n + 1; }; } forEach (missionNamespace getVariable ["BIS_WL_allWarlords", []]);
	GUERRE_votes = (missionNamespace getVariable ["GUERRE_votes", 0]) + 1;
	missionNamespace setVariable [format ["GUERRE_choix_%1", _i], [getPos _c, _n]];
};

GUERRE_fnc_etat_major = {
	params ["_i"];
	[_i] call GUERRE_fnc_voter;
	private _base = [_i] call GUERRE_fnc_base;
	private _vise = [1 - _i] call GUERRE_fnc_cible;
	private _cible = [_i] call GUERRE_fnc_cible;
	private _groupes = (GUERRE_groupes select _i) select { ([_x] call GUERRE_fnc_hommes) > 0 };
	private _garnison = 0;
	private _menace = 0;
	if ((!isNull _base) && { _vise isEqualTo _base }) then {
		_menace = [_i, getPos _base, 1500] call GUERRE_fnc_ennemis_connus;
		_garnison = GUERRE_MIN_DEFENSEURS max (ceil (_menace / GUERRE_RATIO_ASSAUT));
	};
	private _tries = [_groupes, [_base], { (leader _x) distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
	private _n = 0;
	{
		if (_n < _garnison) then { _x setVariable ["GUERRE_role", "garnison"]; _n = _n + ([_x] call GUERRE_fnc_hommes); } else { _x setVariable ["GUERRE_role", "offensive"]; };
	} forEach _tries;
	private _em = [_garnison, _menace, 0, 0, 0, -1, -1];
	if ((!isNull _cible) && { !(_cible isEqualTo _base) }) then {
		private _pc = getPos _cible;
		private _rp = [_i, _cible, _base] call GUERRE_fnc_ralliement;
		private _defenseurs = GUERRE_MIN_DEFENSEURS max ([_i, _pc, 400] call GUERRE_fnc_ennemis_connus);
		private _reunis = 0;
		private _devant = 0;
		{
			if ((_x getVariable ["GUERRE_role", ""]) isEqualTo "offensive") then {
				private _l = leader _x;
				private _h = [_x] call GUERRE_fnc_hommes;
				if (((_l distance2D _rp) < 400) || { (_l distance2D _pc) < 700 }) then { _reunis = _reunis + _h; };
				if ((_l distance2D _pc) < 700) then { _devant = _devant + _h; };
			};
		} forEach _groupes;
		private _cle = format ["GUERRE_assaut_%1", _i];
		private _assaut = (missionNamespace getVariable [_cle, objNull]) isEqualTo _cible;
		if ((!_assaut) && { _reunis >= (GUERRE_RATIO_ASSAUT * _defenseurs) }) then { missionNamespace setVariable [_cle, _cible]; _assaut = true; };
		if (_assaut && { _reunis < _defenseurs }) then { missionNamespace setVariable [_cle, objNull]; _assaut = false; };
		_em = [_garnison, _menace, _defenseurs, _reunis, [0, 1] select _assaut, round (_rp select 0), round (_rp select 1)];
	};
	missionNamespace setVariable [format ["GUERRE_em_%1", _i], _em];
	_em
};

GUERRE_fnc_donner = {
	params ["_g", "_mode", "_pos"];
	private _l = leader _g;
	private _cle = format ["%1|%2|%3", _mode, round (_pos select 0), round (_pos select 1)];
	private _fini = (currentWaypoint _g) >= (count (waypoints _g));
	private _p = getPosATL _l;
	private _immobile = (_p distance2D (_g getVariable ["GUERRE_pos", [0, 0, 0]])) < 5;
	_g setVariable ["GUERRE_pos", _p];
	private _bouge = _mode in ["marche", "assaut", "ralliement"];
	private _n = if (_immobile && _bouge) then { (_g getVariable ["GUERRE_immobile", 0]) + 1 } else { 0 };
	_g setVariable ["GUERRE_immobile", _n];
	private _pareil = (_g getVariable ["GUERRE_cle", ""]) isEqualTo _cle;
	if (_pareil && { (!_fini) || { !_bouge } } && { _n < 3 }) exitWith {};
	if (_pareil && { _fini } && { !_bouge }) exitWith {};
	if ((_n >= 3) && { (_g getVariable ["GUERRE_relances", 0]) >= 2 }) then {
		private _routes = (_l nearRoads 800) select { (_x distance2D _l) >= 15 };
		if ((count _routes) > 0) then {
			private _r = [_routes, [_l], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
			private _q0 = getPosATL (_r select 0);
			private _k = 0;
			{ if (alive _x && { (vehicle _x) isEqualTo _x }) then { _x setPosATL (_q0 vectorAdd [((_k mod 4) * 3) - 4.5, (floor (_k / 4)) * 3, 0]); _k = _k + 1; }; } forEach (units _g);
			GUERRE_degages = (missionNamespace getVariable ["GUERRE_degages", 0]) + 1;
			_g setVariable ["GUERRE_relances", 0];
		};
	};
	_g setVariable ["GUERRE_cle", _cle];
	_g setVariable ["GUERRE_relances", (_g getVariable ["GUERRE_relances", 0]) + 1];
	for "_k" from ((count (waypoints _g)) - 1) to 1 step -1 do { deleteWaypoint [_g, _k]; };
	private _wp = _g addWaypoint [_pos, [150, 40, 60, 40, 40] select (["marche", "assaut", "ralliement", "attente", "garde"] find _mode)];
	_wp setWaypointType (["MOVE", "SAD", "MOVE", "HOLD", "SAD"] select (["marche", "assaut", "ralliement", "attente", "garde"] find _mode));
	_g setCurrentWaypoint _wp;
	if (_mode in ["marche", "ralliement"]) then {
		_g setBehaviour "SAFE"; _g setFormation "COLUMN"; _g setSpeedMode "NORMAL"; _g setCombatMode "YELLOW";
	} else {
		_g setBehaviour "AWARE"; _g setFormation "WEDGE"; _g setSpeedMode ([ "FULL", "LIMITED"] select (_mode in ["attente", "garde"])); _g setCombatMode "RED";
	};
};

GUERRE_fnc_ordre = {
	params ["_i", "_g"];
	private _base = [_i] call GUERRE_fnc_base;
	private _cible = [_i] call GUERRE_fnc_cible;
	private _l = leader _g;
	if ((_g getVariable ["GUERRE_role", "offensive"]) isEqualTo "garnison") exitWith {
		private _pb = getPos _base;
		if ((_l distance2D _pb) > 600) then { [_g, "marche", _pb] call GUERRE_fnc_donner; } else { [_g, "garde", _pb] call GUERRE_fnc_donner; };
	};
	if ((isNull _cible) || { _cible isEqualTo _base }) exitWith { [_g, "attente", getPosATL _l] call GUERRE_fnc_donner; };
	private _pc = getPos _cible;
	private _assaut = (missionNamespace getVariable [format ["GUERRE_assaut_%1", _i], objNull]) isEqualTo _cible;
	if (_assaut) exitWith {
		if ((_l distance2D _pc) > 600) then { [_g, "marche", _pc] call GUERRE_fnc_donner; } else { [_g, "assaut", _pc] call GUERRE_fnc_donner; };
	};
	private _rp = [_i, _cible, _base] call GUERRE_fnc_ralliement;
	if ((_l distance2D _rp) > 300) then { [_g, "ralliement", _rp] call GUERRE_fnc_donner; } else { [_g, "attente", _rp] call GUERRE_fnc_donner; };
};

GUERRE_fnc_commandant = {
	while { true } do {
		{
			private _i = _x;
			GUERRE_groupes set [_i, (GUERRE_groupes select _i) select { ([_x] call GUERRE_fnc_hommes) > 0 }];
			private _base = [_i] call GUERRE_fnc_base;
			if (!isNull _base) then {
				private _viv = [_i] call GUERRE_fnc_vivants;
				private _res = count (GUERRE_reserve select _i);
				private _nveh = { _x getVariable ["GUERRE_vehicule", false] } count (GUERRE_groupes select _i);
				private _ce = GUERRE_COUT_ESCOUADE select _i;
				private _cv = GUERRE_COUT_VEHICULE select _i;
				if (((GUERRE_caisse select _i) >= _ce) && { (_viv + 8) <= GUERRE_PLAFOND_HOMMES } && { _res >= 8 }) then {
					private _g = [_i, _base] call GUERRE_fnc_poser_escouade;
					if (!isNull _g) then {
						GUERRE_caisse set [_i, (GUERRE_caisse select _i) - _ce];
						GUERRE_depense set [_i, (GUERRE_depense select _i) + _ce];
						GUERRE_achats set [_i, (GUERRE_achats select _i) + 1];
					};
				} else {
					private _veut = (_nveh < floor ((GUERRE_achats select _i) / 3)) || { (_viv + 8) > GUERRE_PLAFOND_HOMMES };
					if (_veut && { (GUERRE_caisse select _i) >= _cv } && { (_viv + 3) <= GUERRE_PLAFOND_HOMMES } && { _res >= 3 }) then {
						private _g = [_i, _base] call GUERRE_fnc_poser_vehicule;
						if (!isNull _g) then {
							_g setVariable ["GUERRE_vehicule", true];
							GUERRE_caisse set [_i, (GUERRE_caisse select _i) - _cv];
							GUERRE_depense set [_i, (GUERRE_depense select _i) + _cv];
						};
					};
				};
				[_i] call GUERRE_fnc_etat_major;
				{ [_i, _x] call GUERRE_fnc_ordre; } forEach (GUERRE_groupes select _i);
			};
			{ if (!isPlayer _x && { (side group _x) isEqualTo (GUERRE_CAMPS select _i) }) then { _x setVariable ["BIS_WL_funds", 0, true]; }; } forEach (missionNamespace getVariable ["BIS_WL_allWarlords", []]);
		} forEach [0, 1];
		sleep 20;
	};
};

GUERRE_fnc_tour = {
	params ["_pe", "_pw"];
	{
		private _i = _forEachIndex;
		private _v = _x max 0;
		private _cap = GUERRE_PLAFOND_CAISSE * (GUERRE_COUT_ESCOUADE select _i);
		private _neuf = ((GUERRE_caisse select _i) + _v) min (_cap max (GUERRE_caisse select _i));
		GUERRE_annules set [_i, (GUERRE_annules select _i) + (((GUERRE_caisse select _i) + _v) - _neuf)];
		GUERRE_caisse set [_i, _neuf];
		GUERRE_verse set [_i, (GUERRE_verse select _i) + _v];
		["VERSE", [_i, GUERRE_verse select _i, GUERRE_caisse select _i]] call LABO_R;
		["ANNULE", [_i, round (GUERRE_annules select _i)]] call LABO_R;
	} forEach [_pe, _pw];
	{
		private _p = getPos (_x getVariable ["BIS_WL_sectorZR", _x]);
		private _cote = _x getVariable ["BIS_WL_sectorSide", sideUnknown];
		["ZONE", [round (_p select 0), round (_p select 1), GUERRE_CAMPS find _cote]] call LABO_R;
	} forEach (missionNamespace getVariable ["BIS_WL_sectors", []]);
	{
		private _i = _x;
		["FORCES", [_i, [_i] call GUERRE_fnc_vivants, count (GUERRE_groupes select _i), GUERRE_pertes select _i, GUERRE_depense select _i, GUERRE_achats select _i]] call LABO_R;
		private _c = [_i] call GUERRE_fnc_cible;
		if (isNull _c) then { ["CIBLE", [_i, -1, -1]] call LABO_R; } else { ["CIBLE", [_i, round ((getPos _c) select 0), round ((getPos _c) select 1)]] call LABO_R; };
		["EM", [_i] + (missionNamespace getVariable [format ["GUERRE_em_%1", _i], [0, 0, 0, 0, 0, -1, -1]])] call LABO_R;
	} forEach [0, 1];
	["TEMPS", [round time]] call LABO_R;
};
