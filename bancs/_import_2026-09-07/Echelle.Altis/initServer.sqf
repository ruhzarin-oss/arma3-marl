// =====================================================================
// ECHELLE D'APPRENTISSAGE - BARREAUX B0 et B1, RUNS TEMOINS
// Aucun apprentissage ici. On mesure les trois temoins qui dimensionneront
// la porte : DOCTRINE, ALEATOIRE, NOOP. La barre se pose sur ces nombres.
// =====================================================================

HMT_N       = 17;                              // episodes par (barreau, temoin) et par instance
HMT_D       = 30;                              // PALIER courant, metres
// Budget de temps PROPORTIONNEL a la distance : 75 s pour 150 m, plancher 20 s.
// Sinon un palier court offrirait au hasard bien plus de temps PAR METRE qu'un long,
// et le controle d'alimentation mesurerait ma generosite, pas le palier.
HMT_T       = (20 max (75 * HMT_D / 150));
// Rayon de prise = 10 % de la distance, plancher 6 m. A 150 m la regle rend 15 m :
// elle REPRODUIT exactement la mesure deja faite, elle ne la reecrit pas.
HMT_RAYON   = (6 max (HMT_D / 10));
HMT_CYCLE   = 4;                               // un geste toutes les 4 s
HMT_BARREAUX = ["B0"];
HMT_TEMOINS  = ["DOCTRINE", "ALEATOIRE", "NOOP"];

0 setOvercast 0; 0 setFog 0; forceWeatherChange;
enableSaving [false, false];

// ---------------------------------------------------------------------
// 1. LE SITE SE GELE : recherche DETERMINISTE, aucun tirage.
//    Meme code, meme resultat, a jamais. C'est ca, geler un terrain.
// ---------------------------------------------------------------------
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
HMT_SITE  = +HMT_ANCRE;
HMT_AZ    = 0;
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
					{
						private _h = getTerrainHeightASL _x;
						for "_k" from 0 to 3 do {
							_dev = _dev max (abs ((getTerrainHeightASL (_x getPos [14, _k * 90])) - _h));
						};
					} forEach [_p, _q];
					private _s = _m - _dev * 0.4;
					if (_s > _meilleur) then { _meilleur = _s; HMT_SITE = _p; HMT_AZ = _b; };
				};
			};
		};
	};
};
HMT_OBJ = HMT_SITE getPos [HMT_D, HMT_AZ];   // objectif au PALIER, sur l axe gele
HMT_OBJ set [2, 0];
diag_log format ["[ECH] SITE GELE site=%1 az=%2 obj=%3 alt=%4 degagement=%5 score=%6",
	HMT_SITE, HMT_AZ, HMT_OBJ, round (getTerrainHeightASL HMT_SITE),
	(([HMT_SITE, HMT_OBJ] call HMT_fnc_clear) toFixed 2), (_meilleur toFixed 2)];

// ---------------------------------------------------------------------
// 2. LE CATALOGUE DE GESTES - interface CONSTANTE sur toute l'echelle.
//    13 gestes. L'appui n'y est PAS : il n'a pas d'executeur demontre.
// ---------------------------------------------------------------------
// 0-7  : marcher 40 m dans une des 8 directions absolues
// 8    : marcher 40 m vers l'objectif
// 9    : ENGAGER - designer UNE fois, laisser l'IA native tirer
// 10-12: posture debout / accroupi / couche
HMT_NGESTES = 13;

HMT_fnc_geste = {
	params ["_u", "_g", "_obj", "_enn"];
	if (!alive _u) exitWith {};
	switch (true) do {
		case (_g < 8): {
			_u doMove (_u getPos [40, _g * 45]);
		};
		case (_g == 8): {
			private _d = _u distance2D _obj;
			_u doMove (if (_d < 45) then { _obj } else { _u getPos [40, _u getDir _obj] });
		};
		case (_g == 9): {
			if (!isNull _enn && { alive _enn }) then {
				_u reveal [_enn, 4];
				_u doTarget _enn;          // UNE fois. On ne re-vise pas : ca casse la visee.
			};
		};
		case (_g == 10): { _u setUnitPos "UP" };
		case (_g == 11): { _u setUnitPos "MIDDLE" };
		default          { _u setUnitPos "DOWN" };
	};
};

// ---------------------------------------------------------------------
// 3. LES TROIS TEMOINS - ils choisissent dans LE MEME catalogue
// ---------------------------------------------------------------------
HMT_fnc_choix = {
	params ["_temoin", "_u", "_obj", "_enn", "_engage"];
	switch (_temoin) do {
		case "NOOP":      { -1 };
		case "ALEATOIRE": { floor (random HMT_NGESTES) };
		default {
			// DOCTRINE : l'ordre le plus bete qui vise le bon point final.
			// Designer l'ennemi une seule fois quand il est a portee, puis avancer.
			if (!isNull _enn && { alive _enn } && { !_engage } && { (_u distance2D _enn) < 200 }) then { 9 }
			else { 8 };
		};
	};
};

// ---------------------------------------------------------------------
// 4. UN EPISODE
// ---------------------------------------------------------------------
HMT_fnc_episode = {
	params ["_barreau", "_temoin", "_idx"];

	HMT_coups = 0;

	private _az  = HMT_AZ + (random 12) - 6;
	private _p0  = HMT_SITE getPos [random (HMT_D / 25), random 360];   // jitter proportionnel : 6 m a 150
	_p0 set [2, 0];
	private _obj = _p0 getPos [HMT_D, _az];
	_obj set [2, 0];

	private _ga = createGroup west;
	private _u = _ga createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
	_u setPosATL [_p0 select 0, _p0 select 1, 0];
	_u setDir _az;
	_u setSkill 0.6;
	_u setUnitPos "UP";
	// AUTOCOMBAT RESTE ACTIF. Le couper retire la faculte d'ENGAGER (15/08).
	_ga setBehaviour "AWARE";
	_ga setCombatMode "YELLOW";
	_u addEventHandler ["Fired", { HMT_coups = HMT_coups + 1 }];

	private _enn = objNull;
	private _gd  = grpNull;
	if (_barreau == "B1") then {
		_gd = createGroup east;
		_enn = _gd createUnit ["O_Soldier_F", _obj, [], 0, "NONE"];
		_enn setPosATL [_obj select 0, _obj select 1, 0];
		// immobile et AVEUGLE, mais PAS captif : il doit rester une cible acquerable
		_enn disableAI "PATH";
		_enn disableAI "AUTOTARGET";
		_enn disableAI "TARGET";
		_enn disableAI "AUTOCOMBAT";
		_enn setCombatMode "BLUE";
		_enn setBehaviour "CARELESS";
		_enn setUnitPos "UP";
		_gd setCombatMode "BLUE";
	};

	sleep 2;

	private _t0 = time;
	private _engage = false;
	private _prise = 0;
	while { time - _t0 < HMT_T && _prise == 0 && alive _u } do {
		private _g = [_temoin, _u, _obj, _enn, _engage] call HMT_fnc_choix;
		if (_g >= 0) then {
			[_u, _g, _obj, _enn] call HMT_fnc_geste;
			if (_g == 9) then { _engage = true };
		};
		private _k = 0;
		while { _k < HMT_CYCLE && _prise == 0 && alive _u } do {
			sleep 0.5;
			_k = _k + 0.5;
			private _arrive = (_u distance2D _obj) < HMT_RAYON;
			if (_barreau == "B0") then {
				if (_arrive) then { _prise = 1 };
			} else {
				if (_arrive && { !alive _enn }) then { _prise = 1 };
			};
		};
	};

	private _duree   = time - _t0;
	private _dfin    = round (_u distance2D _obj);
	private _emort   = if (_barreau == "B1") then { if (alive _enn) then { 0 } else { 1 } } else { -1 };
	private _vivant  = if (alive _u) then { 1 } else { 0 };

	private _ligne = format ["barreau=%1 temoin=%2 idx=%3 prise=%4 duree=%5 dfin=%6 ennemi_mort=%7 vivant=%8 coups=%9",
		_barreau, _temoin, _idx, _prise, (_duree toFixed 1), _dfin, _emort, _vivant, HMT_coups];

	{ if (!isNull _x) then { deleteVehicle _x } } forEach [_u, _enn];
	deleteGroup _ga;
	if (!isNull _gd) then { deleteGroup _gd };

	_ligne
};

// ---------------------------------------------------------------------
// 5. LA SERIE - entrelacee sur les temoins ET les barreaux
// ---------------------------------------------------------------------
[] spawn {
	sleep 5;
	diag_log format ["[ECH] DEBUT n=%1 T=%2s D=%3m rayon=%4m cycle=%5s gestes=%6",
		HMT_N, HMT_T, HMT_D, HMT_RAYON, HMT_CYCLE, HMT_NGESTES];
	for "_i" from 0 to (HMT_N - 1) do {
		{
			private _b = _x;
			{
				private _r = [_b, _x, _i] call HMT_fnc_episode;
				diag_log format ["[ECH] %1", _r];
				sleep 1;
			} forEach HMT_TEMOINS;
		} forEach HMT_BARREAUX;
	};
	diag_log "[ECH] FIN";
};
