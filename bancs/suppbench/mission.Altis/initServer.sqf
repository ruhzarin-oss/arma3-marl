// =====================================================================
// BANC E0 - GESTE N.1 : doSuppressiveFire
// Protocole pre-inscrit. Trois conditions entrelacees A,B,C,A,B,C...
// A = ordre de suppression | B = feu direct (controle positif) | C = rien
// =====================================================================

HMT_N      = 20;   // runs par condition
HMT_WINDOW = 30;   // secondes de mesure
HMT_RANGE  = 130;  // metres entre les deux lignes
HMT_CONDS  = ["A", "B", "C", "D", "E"];

0 setOvercast 0; 0 setFog 0; forceWeatherChange;
enableSaving [false, false];

// --------- le site ET l'azimut se choisissent sur le DEGAGEMENT ------
// Un site plat sur 25 m ne dit rien de la ligne de 130 m. On mesure la
// marge de la ligne de vue au-dessus du terrain, et on prend la meilleure.
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

HMT_site = [8291.45, 10065.42, 0];
HMT_az0  = 0;
private _bestClear = -1e9;
for "_c" from 1 to 60 do {
	private _p = [8291.45, 10065.42, 0] getPos [sqrt(random 1) * 400, random 360];
	_p set [2, 0];
	if (!surfaceIsWater _p && { (count (nearestObjects [_p, ["House"], 100])) == 0 }) then {
		for "_b" from 0 to 350 step 10 do {
			private _q = _p getPos [130, _b];
			if (!surfaceIsWater _q && { (count (nearestObjects [_q, ["House"], 60])) == 0 }) then {
				private _m = [_p, _q] call HMT_fnc_clear;
				// on veut aussi les deux bouts plats
				private _dev = 0;
				{
					private _h = getTerrainHeightASL _x;
					for "_k" from 0 to 3 do {
						_dev = _dev max (abs ((getTerrainHeightASL (_x getPos [12, _k * 90])) - _h));
					};
				} forEach [_p, _q];
				private _score = _m - _dev * 0.5;
				if (_score > _bestClear) then { _bestClear = _score; HMT_site = _p; HMT_az0 = _b; };
			};
		};
	};
};
HMT_site set [2, 0];
HMT_clear0 = [HMT_site, HMT_site getPos [130, HMT_az0]] call HMT_fnc_clear;
diag_log format ["[SUPP] site=%1 alt=%2 az0=%3 degagement=%4 m maisons_100m=%5",
	HMT_site, round (getTerrainHeightASL HMT_site), HMT_az0, (HMT_clear0 toFixed 2),
	count (nearestObjects [HMT_site, ["House"], 100])];

// --------- decalage lateral propre ------------------------------------
HMT_fnc_off = {
	params ["_c", "_lat", "_az"];
	[(_c select 0) + _lat * sin (_az + 90), (_c select 1) + _lat * cos (_az + 90), 0]
};

// =====================================================================
// UN RUN
// =====================================================================
HMT_fnc_run = {
	params ["_cond", "_idx"];

	HMT_cFired = 0; HMT_cSupp = 0; HMT_cHit = 0; HMT_cDef = 0;

	private _az = HMT_az0 + (random 16) - 8;
	private _cD = HMT_site getPos [random 6, random 360];
	_cD set [2, 0];
	private _cA = _cD getPos [HMT_RANGE + (random 10) - 5, _az];
	_cA set [2, 0];

	// ---- defenseurs, chacun derriere un abri, jambes coupees
	private _gd = createGroup east;
	private _def = []; private _props = [];
	{
		private _p = [_cD, _x, _az] call HMT_fnc_off;
		private _b = createVehicle ["Land_BagBunker_Small_F", _p, [], 0, "CAN_COLLIDE"];
		_b setDir _az;
		_b setPosATL [_p select 0, _p select 1, 0];
		_props pushBack _b;
		private _q = _p getPos [2.2, _az + 180];
		private _u = _gd createUnit ["O_Soldier_F", _q, [], 0, "NONE"];
		_u setPosATL [_q select 0, _q select 1, 0];
		_u disableAI "PATH";
		_u setUnitPos "MIDDLE";
		_u setSkill 0.6;
		_def pushBack _u;
	} forEach [-9, -3, 3, 9];
	_gd setBehaviour "AWARE";
	_gd setCombatMode "YELLOW";

	// ---- attaquants, arme d'appui, invulnerables (sinon C tronque le run)
	private _ga = createGroup west;
	private _att = [];
	{
		private _p = [_cA, _x, _az] call HMT_fnc_off;
		private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
		_u setPosATL [_p select 0, _p select 1, 0];
		removeAllWeapons _u;
		_u addBackpack "B_Carryall_blk";
		for "_i" from 1 to 4 do { _u addItemToBackpack "200Rnd_65x39_cased_Box" };
		_u addWeapon "LMG_Mk200_F";
		_u allowDamage false;
		_u disableAI "PATH";
		_u setUnitPos "MIDDLE";
		_u setSkill 0.6;
		_att pushBack _u;
	} forEach [-9, -3, 3, 9];
	_ga setBehaviour "AWARE";

	// ---- bridage
	// A, C, D : brides (aucun tir spontane possible)
	// B       : libre + ennemis reveles  -> controle positif de l'instrument
	// E       : libre + ennemis CAPTIFS  -> pas de tir spontane, pas de bride
	if (_cond in ["A", "C", "D"]) then {
		{ _x disableAI "AUTOTARGET"; _x disableAI "TARGET"; } forEach _att;
		_ga setCombatMode "YELLOW";
	};
	if (_cond == "B") then {
		_ga setCombatMode "RED";
		_ga setBehaviour "COMBAT";
		{ private _a = _x; { _a reveal [_x, 4] } forEach _def; } forEach _att;
	};
	if (_cond == "E") then {
		{ _x setCaptive true } forEach _def;
		_ga setCombatMode "YELLOW";
	};

	// ---- capteurs
	{ _x addEventHandler ["Fired",     { HMT_cFired = HMT_cFired + 1 }] } forEach _att;
	{ _x addEventHandler ["Fired",     { HMT_cDef   = HMT_cDef   + 1 }] } forEach _def;
	{ _x addEventHandler ["Suppressed",{ HMT_cSupp  = HMT_cSupp  + 1 }] } forEach _def;
	{ _x addEventHandler ["HitPart",   { HMT_cHit   = HMT_cHit   + 1 }] } forEach _def;

	sleep 3;   // le monde se pose

	// --- diagnostic : sans ca, un zero est illisible
	private _a0 = _att select 0;
	private _d0 = _def select 0;
	diag_log format ["[DIAG] cond=%1 arme=%2 charg=%3 munitions=%4 sait=%5 voit=%6 dist=%7",
		_cond, primaryWeapon _a0, count (primaryWeaponMagazine _a0), someAmmo _a0,
		((_a0 knowsAbout _d0) toFixed 2),
		(([_a0, "VIEW"] checkVisibility [eyePos _a0, eyePos _d0]) toFixed 2),
		round (_a0 distance _d0)];
	diag_log format ["[DIAG] cond=%1 degagement_run=%2 m", _cond, (([_cD, _cA] call HMT_fnc_clear) toFixed 2)];

	private _t0 = time;

	// ---- l'ordre, re-emis : doSuppressiveFire est une rafale, pas un etat
	if (_cond in ["A", "E"]) then {
		[_att, _cD, _t0] spawn {
			params ["_att", "_pos", "_t0"];
			while { time - _t0 < HMT_WINDOW } do {
				{ if (alive _x) then { _x doSuppressiveFire _pos } } forEach _att;
				sleep 4;
			};
		};
	};

	// D : meme bride qu'en A, mais ordre de tir ORDINAIRE sur une cible.
	// Si D tire et A non, ce n'est pas la bride : c'est doSuppressiveFire.
	if (_cond == "D") then {
		[_att, _def, _t0] spawn {
			params ["_att", "_def", "_t0"];
			while { time - _t0 < HMT_WINDOW } do {
				private _vivants = _def select { alive _x };
				if (count _vivants > 0) then {
					private _tg = _vivants select 0;
					{ if (alive _x) then { _x doTarget _tg; _x doFire _tg; }; } forEach _att;
				};
				sleep 3;
			};
		};
	};

	// ---- fenetre de mesure
	private _sum = 0; private _n = 0; private _max = 0; private _tick = 0;
	while { time - _t0 < HMT_WINDOW } do {
		{
			if (alive _x) then {
				private _s = getSuppression _x;
				_sum = _sum + _s; _n = _n + 1;
				if (_s > _max) then { _max = _s };
			};
		} forEach _def;
		_tick = _tick + 1;
		if ((_tick % 6) == 0) then { { _x setVehicleAmmo 1 } forEach _att };  // munitions jamais limitantes
		sleep 0.5;
	};

	private _supMean = if (_n > 0) then { _sum / _n } else { -1 };
	private _dead = count (_def select { !alive _x });

	private _line = format ["cond=%1 idx=%2 fired=%3 supMean=%4 supMax=%5 supp=%6 hit=%7 deffired=%8 dead=%9",
		_cond, _idx, HMT_cFired, (_supMean toFixed 4), (_max toFixed 3), HMT_cSupp, HMT_cHit, HMT_cDef, _dead];

	// ---- menage
	{ deleteVehicle _x } forEach (_def + _att + _props);
	deleteGroup _gd; deleteGroup _ga;

	_line
};

// =====================================================================
// LA SERIE - entrelacee, pour qu'aucune derive du serveur ne frappe
// une seule condition
// =====================================================================
[] spawn {
	sleep 5;
	diag_log format ["[SUPP] DEBUT n=%1 fenetre=%2s portee=%3m", HMT_N, HMT_WINDOW, HMT_RANGE];
	for "_i" from 0 to (HMT_N - 1) do {
		{
			private _r = [_x, _i] call HMT_fnc_run;
			diag_log format ["[SUPP] %1", _r];
			sleep 2;
		} forEach HMT_CONDS;
	};
	diag_log "[SUPP] FIN";
};
