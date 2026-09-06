// =====================================================================
// R2 — RE-MESURER LE CONTRASTE VU / NON-VU, APRES LE BALAYAGE BLUE
//
// L'ancre x1,75 vient de 563 000 observations SURSITAIRES : elles ont ete prises quand
// les attaquants portaient `combatMode BLUE` et ne combattaient pas. On ne calibre pas
// un gymnase sur une ancre morte. Ici les attaquants COMBATTENT.
//
// LA PRIMITIVE A CHANGE. `checkVisibility` rend 0,000 sur serveur dedie, y compris a
// 5 m sur terrain plat — mesure du 30/08, controle imparable. On lit desormais la vue
// par `lineIntersectsSurfaces` en LOD VIEW, qui separe les bras ET nomme l'obstacle.
// =====================================================================

HMT_N     = 10;    // episodes par instance
HMT_T     = 120;   // duree max d'un episode
HMT_D     = 150;   // distance de depart
HMT_A     = 8;     // attaquants
HMT_DEF   = 6;     // defenseurs

0 setOvercast 0; 0 setFog 0; forceWeatherChange;
enableSaving [false, false];

// ---------------------------------------------------------------------
// LA VUE — la primitive reparee
// ---------------------------------------------------------------------
HMT_fnc_vue = {
	params ["_obs", "_cible"];
	private _po = getPosASL _obs; private _pc = getPosASL _cible;
	private _eo = [_po select 0, _po select 1, (_po select 2) + 1.5];   // oeil de l'observateur
	private _ec = [_pc select 0, _pc select 1, (_pc select 2) + 1.0];   // buste de la cible
	(count (lineIntersectsSurfaces [_eo, _ec, _obs, _cible, true, 1, "VIEW", "VIEW"])) == 0
};

// ---------------------------------------------------------------------
// LE SITE SE RE-GELE — critere verifie PAR LE MOTEUR, pas par une liste de classes.
// L'ancien excluait la classe `House` ; un ficus passait au travers et coupait la vue.
// ---------------------------------------------------------------------
HMT_fnc_ligneLibre = {
	params ["_p", "_q"];
	private _a = [_p select 0, _p select 1, (getTerrainHeightASL _p) + 1.5];
	private _b = [_q select 0, _q select 1, (getTerrainHeightASL _q) + 1.5];
	if (terrainIntersectASL [_a, _b]) exitWith { false };
	(count (lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "VIEW", "VIEW"])) == 0
};

HMT_ANCRE = [8291.45, 10065.42, 0];
HMT_SITE = +HMT_ANCRE; HMT_AZ = -1;
private _trouve = false;
for "_gx" from -7 to 7 do {
	for "_gy" from -7 to 7 do {
		if (!_trouve) then {
			private _p = [(HMT_ANCRE select 0) + _gx * 50, (HMT_ANCRE select 1) + _gy * 50, 0];
			if (!surfaceIsWater _p) then {
				for "_b" from 0 to 350 step 10 do {
					if (!_trouve) then {
						private _q = _p getPos [HMT_D, _b];
						if (!surfaceIsWater _q && { [_p, _q] call HMT_fnc_ligneLibre }) then {
							// on exige aussi les DEUX TIERS de la largeur libres : le banc
							// place huit hommes de front, pas un seul.
							private _ok = true;
							{
								private _p2 = [_p, _x, _b] call { params ["_c","_lat","_az"];
									[(_c select 0) + _lat * sin (_az + 90), (_c select 1) + _lat * cos (_az + 90), 0] };
								private _q2 = [_q, _x, _b] call { params ["_c","_lat","_az"];
									[(_c select 0) + _lat * sin (_az + 90), (_c select 1) + _lat * cos (_az + 90), 0] };
								if (!([_p2, _q2] call HMT_fnc_ligneLibre)) then { _ok = false };
							} forEach [-14, -7, 7, 14];
							if (_ok) then { _trouve = true; HMT_SITE = _p; HMT_AZ = _b; };
						};
					};
				};
			};
		};
	};
};
HMT_SITE set [2, 0];
HMT_OBJ = HMT_SITE getPos [HMT_D, HMT_AZ];
HMT_OBJ set [2, 0];
diag_log format ["[R2] SITE trouve=%1 site=%2 az=%3 obj=%4 alt=%5",
	_trouve, HMT_SITE, HMT_AZ, HMT_OBJ, round (getTerrainHeightASL HMT_SITE)];

HMT_fnc_off = {
	params ["_c", "_lat", "_az"];
	[(_c select 0) + _lat * sin (_az + 90), (_c select 1) + _lat * cos (_az + 90), 0]
};

// ---------------------------------------------------------------------
// UN EPISODE
// ---------------------------------------------------------------------
// ⚠️ STRATIFICATION PAR DISTANCE — sans elle la mesure est FAUSSE.
// « Non vu » est confondu avec « loin » : au depart les huit hommes sont a 150 m,
// invisibles ET hors de danger. Un contraste brut compterait cette distance comme
// une protection du couvert. On compte donc DANS des tranches de distance.
HMT_TRANCHES = [40, 80, 120, 999];    // bornes hautes, en metres
HMT_obsVu  = [0,0,0,0]; HMT_obsNon  = [0,0,0,0];
HMT_mortVu = [0,0,0,0]; HMT_mortNon = [0,0,0,0];
HMT_tirsDef = 0;
HMT_fnc_tranche = {
	params ["_d"];
	private _k = 3;
	{ if (_d < _x && { _k == 3 }) then { _k = _forEachIndex } } forEach HMT_TRANCHES;
	_k
};

HMT_fnc_episode = {
	params ["_idx"];
	private _az = HMT_AZ;
	private _cD = +HMT_OBJ;
	private _cA = +HMT_SITE;
	private _props = [];

	// --- couvert deliberement disperse au tiers median : sans lui, la condition
	//     « non vu » n'existe pas et la mesure ne peut pas separer.
	for "_i" from 0 to 23 do {
		private _d = 45 + random 70;
		private _lat = (random 44) - 22;
		private _base = _cA getPos [_d, _az];
		private _p = [_base, _lat, _az] call HMT_fnc_off;
		private _o = createVehicle ["Land_BagFence_Long_F", _p, [], 0, "CAN_COLLIDE"];
		_o setDir (_az + (random 60) - 30);
		_o setPosATL [_p select 0, _p select 1, 0];
		_props pushBack _o;
	};

	// --- defenseurs : ils tiennent, ils tirent
	private _gd = createGroup east;
	private _def = [];
	for "_i" from 0 to (HMT_DEF - 1) do {
		private _p = [_cD, (_i - 2.5) * 7, _az] call HMT_fnc_off;
		private _b = createVehicle ["Land_BagBunker_Small_F", _p, [], 0, "CAN_COLLIDE"];
		_b setDir (_az + 180); _b setPosATL [_p select 0, _p select 1, 0];
		_props pushBack _b;
		private _q = _p getPos [2.2, _az];
		private _u = _gd createUnit ["O_Soldier_F", _q, [], 0, "NONE"];
		_u setPosATL [_q select 0, _q select 1, 0];
		_u disableAI "PATH"; _u setUnitPos "MIDDLE"; _u setSkill 0.55;
		_u addEventHandler ["Fired", { HMT_tirsDef = HMT_tirsDef + 1 }];
		_def pushBack _u;
	};
	_gd setBehaviour "COMBAT"; _gd setCombatMode "RED";

	// --- attaquants : ils COMBATTENT. C'est toute la difference avec l'ancre morte.
	private _ga = createGroup west;
	private _att = [];
	for "_i" from 0 to (HMT_A - 1) do {
		private _p = [_cA, (_i - 3.5) * 6, _az] call HMT_fnc_off;
		private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
		_u setPosATL [_p select 0, _p select 1, 0];
		_u setSkill 0.55;
		_att pushBack _u;
	};
	_ga setBehaviour "COMBAT"; _ga setCombatMode "RED"; _ga setSpeedMode "NORMAL";
	{ _x doMove HMT_OBJ } forEach _att;

	sleep 3;

	// --- echantillonnage a 1 Hz : etat de VUE de chaque vivant, puis sa mort
	private _t0 = time;
	private _etat = []; { _etat pushBack -1 } forEach _att;   // -1 inconnu, 0 non vu, 1 vu
	private _tr   = []; { _tr   pushBack 3 } forEach _att;    // tranche de distance au dernier releve
	private _mort = []; { _mort pushBack false } forEach _att;
	while { time - _t0 < HMT_T } do {
		{
			private _i = _forEachIndex;
			if (!(_mort select _i)) then {
				if (!alive _x) then {
					// il vient de mourir : on impute a son DERNIER etat observe
					_mort set [_i, true];
					private _e = _etat select _i;
					private _k = _tr select _i;
					if (_e == 1) then { HMT_mortVu set [_k, (HMT_mortVu select _k) + 1] };
					if (_e == 0) then { HMT_mortNon set [_k, (HMT_mortNon select _k) + 1] };
				} else {
					private _cible = _att select _i;
					private _vu = false;
					private _dmin = 1e6;
					{
						if (alive _x) then {
							private _dd = _x distance2D _cible;
							if (_dd < _dmin) then { _dmin = _dd };
							if (!_vu && { [_x, _cible] call HMT_fnc_vue }) then { _vu = true };
						};
					} forEach _def;
					private _k = [_dmin] call HMT_fnc_tranche;
					_etat set [_i, if (_vu) then { 1 } else { 0 }];
					_tr set [_i, _k];
					if (_vu) then { HMT_obsVu set [_k, (HMT_obsVu select _k) + 1] }
					      else { HMT_obsNon set [_k, (HMT_obsNon select _k) + 1] };
				};
			};
		} forEach _att;
		if (({ alive _x } count _att) == 0) exitWith {};
		sleep 1;
	};

	private _viv = { alive _x } count _att;
	diag_log format ["[R2] ep=%1 vivants=%2/%3 obsVu=%4 obsNon=%5 mortVu=%6 mortNon=%7 tirsDef=%8",
		_idx, _viv, HMT_A, HMT_obsVu, HMT_obsNon, HMT_mortVu, HMT_mortNon, HMT_tirsDef];

	{ if (!isNull _x) then { deleteVehicle _x } } forEach (_att + _def + _props);
	deleteGroup _ga; deleteGroup _gd;
};

[] spawn {
	sleep 5;
	if (HMT_AZ < 0) exitWith { diag_log "[R2] AUCUN SITE A LIGNE LIBRE — banc arrete" };
	diag_log format ["[R2] DEBUT n=%1 T=%2 D=%3 A=%4 DEF=%5", HMT_N, HMT_T, HMT_D, HMT_A, HMT_DEF];
	for "_i" from 0 to (HMT_N - 1) do { [_i] call HMT_fnc_episode; sleep 2; };
	{
		private _k = _forEachIndex;
		private _ov = HMT_obsVu select _k;  private _on = HMT_obsNon select _k;
		private _mv = HMT_mortVu select _k; private _mn = HMT_mortNon select _k;
		private _pv = if (_ov > 0) then { _mv / _ov } else { -1 };
		private _pn = if (_on > 0) then { _mn / _on } else { -1 };
		diag_log format ["[R2] TRANCHE <%1 m : obsVu=%2 mortVu=%3 pVu=%4 | obsNon=%5 mortNon=%6 pNon=%7 | contraste=%8",
			_x, _ov, _mv, (_pv toFixed 5), _on, _mn, (_pn toFixed 5),
			(if (_pn > 0) then { (_pv / _pn) toFixed 3 } else { "n/a" })];
	} forEach HMT_TRANCHES;
	diag_log format ["[R2] tirsDef=%1", HMT_tirsDef];
	diag_log "[R2] FIN";
};
