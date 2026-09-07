// =====================================================================
// SONDE DE VUE — quelle formulation de la ligne de vue DIT LA VERITE ?
//
// Ce soir, mon appel `[_a, "VIEW"] checkVisibility [eyePos _a, eyePos _d]` a rendu 0,00
// pendant des runs ou les deux camps se tiraient dessus. Une colonne fausse. Or c'est
// cette primitive qui definit « etre vu », donc l'ancre du x1,75, donc toute la
// calibration du gymnase. On ne repare pas une ancre avec un instrument muet.
//
// LE DISPOSITIF, et il a un CONTROLE POSITIF ET NEGATIF PAR CONSTRUCTION :
//   bras DEGAGE  — deux hommes a 60 m, terrain plat certifie, rien entre eux.
//   bras MUR     — les MEMES hommes, un mur de beton pose au milieu.
// Une formulation qui ne separe pas ces deux bras est MORTE, quel que soit son elegance.
// Verite de terrain independante : on demande AUSSI au moteur lui-meme, par `lineIntersectsSurfaces`
// et par le fait qu'un tireur touche ou non sa cible.
// =====================================================================

0 setOvercast 0; 0 setFog 0; forceWeatherChange;

// --- le site gele de l'echelle, recherche deterministe (memes constantes) ---
HMT_fnc_clear = {
	params ["_from", "_to"];
	private _hF = (getTerrainHeightASL _from) + 1.6;
	private _hT = (getTerrainHeightASL _to) + 1.6;
	private _min = 1e9;
	for "_i" from 1 to 29 do {
		private _t = _i / 30;
		private _p = [(_from select 0) + ((_to select 0) - (_from select 0)) * _t,
		              (_from select 1) + ((_to select 1) - (_from select 1)) * _t, 0];
		_min = _min min ((_hF + (_hT - _hF) * _t) - (getTerrainHeightASL _p));
	};
	_min
};
HMT_ANCRE = [8291.45, 10065.42, 0];
HMT_SITE = +HMT_ANCRE; HMT_AZ = 0;
private _meilleur = -1e9;
for "_gx" from -6 to 6 do {
	for "_gy" from -6 to 6 do {
		private _p = [(HMT_ANCRE select 0) + _gx * 55, (HMT_ANCRE select 1) + _gy * 55, 0];
		if (!surfaceIsWater _p && { (count (nearestObjects [_p, ["House"], 110])) == 0 }) then {
			for "_b" from 0 to 350 step 10 do {
				private _q = _p getPos [150, _b];
				if (!surfaceIsWater _q && { (count (nearestObjects [_q, ["House"], 80])) == 0 }) then {
					private _m = [_p, _q] call HMT_fnc_clear;
					private _dev = 0;
					{ private _h = getTerrainHeightASL _x;
					  for "_k" from 0 to 3 do { _dev = _dev max (abs ((getTerrainHeightASL (_x getPos [14, _k * 90])) - _h)); };
					} forEach [_p, _q];
					private _s = _m - _dev * 0.4;
					if (_s > _meilleur) then { _meilleur = _s; HMT_SITE = _p; HMT_AZ = _b; };
				};
			};
		};
	};
};
HMT_SITE set [2, 0];
diag_log format ["[VUE] site=%1 az=%2 degagement=%3",
	HMT_SITE, HMT_AZ, (([HMT_SITE, HMT_SITE getPos [150, HMT_AZ]] call HMT_fnc_clear) toFixed 2)];

// --- checkVisibility EST-IL VIVANT SANS JOUEUR ? Trois controles emboites ----
// Le tour precedent l'a vu a 0,000 meme a 5 m — mais ma ligne de controle portait une
// erreur de parsing, donc ce zero n'etait pas lisible. On refait, sans arithmetique
// dans les tableaux, et avec trois controles dont un que RIEN ne peut faire echouer.
HMT_fnc_mesures = {
	params ["_a", "_b"];
	private _xa = getPosASL _a; private _xb = getPosASL _b;
	private _za = (getTerrainHeightASL (getPos _a)) + 1.6;
	private _zb = (getTerrainHeightASL (getPos _b)) + 1.6;
	private _ma = [_xa select 0, _xa select 1, _za];
	private _mb = [_xb select 0, _xb select 1, _zb];
	private _x5 = (_xa select 0) + 5;
	private _p5 = [_x5, _xa select 1, _za];
	private _p1 = [_xa select 0, _xa select 1, _za + 0.1];

	private _v60 = [_a, _b] checkVisibility [_ma, _mb];
	private _v5  = [_a, _b] checkVisibility [_ma, _p5];
	private _v0  = [objNull, objNull] checkVisibility [_ma, _p1];   // 10 cm : RIEN ne peut bloquer

	private _surf = lineIntersectsSurfaces [_ma, _mb, _a, _b, true, 1, "VIEW", "VIEW"];
	private _qui = "aucun";
	if (count _surf > 0) then {
		private _o = (_surf select 0) select 2;
		_qui = if (isNull _o) then { "nul" } else { typeOf _o };
		if (_qui isEqualTo "") then { _qui = str _o };
	};
	diag_log format ["[VUE-CTRL] ma=%1 mb=%2 p5=%3 p1=%4", str _ma, str _mb, str _p5, str _p1];
	[_v60, _v5, _v0, count _surf, _qui, _b knowsAbout _a]
};

[] spawn {
	sleep 5;
	private _c = HMT_SITE;
	{
		_x params ["_bras", "_avecMur"];
		private _pa = _c getPos [30, HMT_AZ];
		private _pb = _c getPos [30, HMT_AZ + 180];
		private _ga = createGroup west; private _gb = createGroup east;
		private _a = _ga createUnit ["B_Soldier_F", _pa, [], 0, "NONE"];
		private _b = _gb createUnit ["O_Soldier_F", _pb, [], 0, "NONE"];
		{ _x setPosATL [(_pa select 0), (_pa select 1), 0] } forEach [_a];
		_a setPosATL [_pa select 0, _pa select 1, 0];
		_b setPosATL [_pb select 0, _pb select 1, 0];
		{ _x disableAI "PATH"; _x setUnitPos "UP"; _x allowDamage false; } forEach [_a, _b];
		_a setDir (_a getDir _b); _b setDir (_b getDir _a);
		private _mur = objNull;
		if (_avecMur) then {
			_mur = createVehicle ["Land_CncBarrierMedium_F", _c, [], 0, "CAN_COLLIDE"];
			_mur setDir (HMT_AZ + 90);
			_mur setPosATL [_c select 0, _c select 1, 0];
			// un mur de 1 m ne coupe pas une vue d'oeil a 1,6 m : on empile
			for "_i" from 1 to 3 do {
				private _m2 = createVehicle ["Land_CncBarrierMedium_F", _c, [], 0, "CAN_COLLIDE"];
				_m2 setDir (HMT_AZ + 90);
				_m2 setPosATL [_c select 0, _c select 1, 1.0 * _i];
			};
		};
		sleep 4;
		private _m = [_a, _b] call HMT_fnc_mesures;
		diag_log format ["[VUE] bras=%1 dist=%2 chkVis_60m=%3 chkVis_5m=%4 chkVis_10cm=%5 obstacles_VIEW=%6 QUI=%7 knowsAbout=%8",
			_bras, round (_a distance _b),
			((_m select 0) toFixed 3), ((_m select 1) toFixed 3), ((_m select 2) toFixed 3),
			(_m select 3), (_m select 4), ((_m select 5) toFixed 2)];
		{ if (!isNull _x) then { deleteVehicle _x } } forEach [_a, _b];
		{ deleteVehicle _x } forEach (nearestObjects [_c, ["Land_CncBarrierMedium_F"], 20]);
		deleteGroup _ga; deleteGroup _gb;
		sleep 2;
	} forEach [["DEGAGE", false], ["MUR", true], ["DEGAGE_2", false], ["MUR_2", true]];
	diag_log "[VUE] FIN";
};
