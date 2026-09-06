// =====================================================================
// R2-BIS — COUVERT CONTRE MASQUE, et l'un ne se fabrique pas
//
// R2 a mesure un contraste de 12,5x a 40-80 m, contre une ancre de 1,75x. Fable a
// trouve le defaut : mes non-vus etaient derriere du BETON — invisibles ET imperceables.
// Le corpus de l'ancienne ancre etait de nuit : ses non-vus etaient invisibles mais
// BALISTIQUEMENT NUS. Les deux mesures peuvent etre vraies ensemble.
//
// ⛔ ON NE PEUT PAS FABRIQUER UN MASQUE. Sonde du 30/08 sur 20 classes creables : tout
// objet qui bloque le LOD VIEW bloque aussi le LOD FIRE. Il n'existe pas d'objet-masque
// creable. Le masque doit donc etre TROUVE : une ligne coupee par la vegetation du
// terrain, qui arrete la vue et laisse passer les balles.
//
// LE CRITERE EST UNE MESURE. Pour chaque ligne candidate on interroge le moteur deux
// fois : LOD VIEW et LOD FIRE.
//     VIEW bloque + FIRE libre   -> MASQUE
//     VIEW bloque + FIRE bloque  -> COUVERT
//     ni l'un ni l'autre         -> LIBRE
//     le terrain bloque          -> TERRAIN (site rejete)
//
// QUATRE BRAS, deux mesures et deux controles :
//   COUVERT : site clair + sacs de sable  — non-vus blindes
//   MASQUE  : site vegetalise, aucun objet pose — non-vus nus
//   NU      : site clair, rien             — controle : peu de non-vus, contraste ~1
//   AVEUGLE : site clair + sacs, defenseurs incapables d'engager — mortalite ~0
//
// PRE-INSCRIT AVANT LA SERIE : strate decisive 40-80 m. Grandeur = contraste
// p(mort|vu)/p(mort|non-vu), IC95 Wilson. Prediction de Fable, ecrite avant :
// au bras MASQUE le contraste d'Arma sera FAIBLE ; celui du gymnase, infini.
// =====================================================================

HMT_BRAS  = ["COUVERT", "MASQUE", "NU", "AVEUGLE"];
HMT_NBRAS = [8, 8, 5, 4];
HMT_T     = 120;
HMT_D     = 150;
HMT_A     = 8;
HMT_DEF   = 6;
HMT_TRANCHES = [40, 80, 120, 999];
HMT_LATS  = [-14, -7, 0, 7, 14];

0 setOvercast 0; 0 setFog 0; forceWeatherChange;
enableSaving [false, false];

HMT_fnc_off = {
	params ["_c", "_lat", "_az"];
	[(_c select 0) + _lat * sin (_az + 90), (_c select 1) + _lat * cos (_az + 90), 0]
};
HMT_fnc_tranche = {
	params ["_d"];
	private _k = 3;
	{ if (_d < _x && { _k == 3 }) then { _k = _forEachIndex } } forEach HMT_TRANCHES;
	_k
};

// --- LA VUE : lineIntersectsSurfaces. checkVisibility rend 0,000 sans client.
HMT_fnc_vue = {
	params ["_obs", "_cible"];
	private _po = getPosASL _obs; private _pc = getPosASL _cible;
	private _eo = [_po select 0, _po select 1, (_po select 2) + 1.5];
	private _ec = [_pc select 0, _pc select 1, (_pc select 2) + 1.0];
	(count (lineIntersectsSurfaces [_eo, _ec, _obs, _cible, true, 1, "VIEW", "VIEW"])) == 0
};

// --- LE MOTEUR CLASSE LA LIGNE
HMT_fnc_typeLigne = {
	params ["_p", "_q"];
	private _a = [_p select 0, _p select 1, (getTerrainHeightASL _p) + 1.6];
	private _b = [_q select 0, _q select 1, (getTerrainHeightASL _q) + 1.6];
	if (terrainIntersectASL [_a, _b]) exitWith { "TERRAIN" };
	private _v = count (lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "VIEW", "VIEW"]);
	private _f = count (lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "FIRE", "FIRE"]);
	if (_v > 0 && { _f == 0 }) exitWith { "MASQUE" };
	if (_v > 0) exitWith { "COUVERT" };
	"LIBRE"
};

// --- profil des cinq lignes du front
HMT_fnc_profil = {
	params ["_p", "_az"];
	private _n = [0,0,0,0];   // LIBRE, MASQUE, COUVERT, TERRAIN
	{
		private _p2 = [_p, _x, _az] call HMT_fnc_off;
		private _q2 = [(_p getPos [HMT_D, _az]), _x, _az] call HMT_fnc_off;
		private _t = [_p2, _q2] call HMT_fnc_typeLigne;
		private _k = ["LIBRE","MASQUE","COUVERT","TERRAIN"] find _t;
		_n set [_k, (_n select _k) + 1];
	} forEach HMT_LATS;
	_n
};

// ---------------------------------------------------------------------
// DEUX SITES, cherches DETERMINISTIQUEMENT sur la meme grille
// ---------------------------------------------------------------------
HMT_ANCRE = [8291.45, 10065.42, 0];

// --- SITE CLAIR : les cinq lignes du front libres. Recherche deterministe.
HMT_SITE_CLAIR = []; HMT_AZ_CLAIR = -1;
for "_gx" from -8 to 8 do {
	for "_gy" from -8 to 8 do {
		private _p = [(HMT_ANCRE select 0) + _gx * 50, (HMT_ANCRE select 1) + _gy * 50, 0];
		if (!surfaceIsWater _p && { HMT_AZ_CLAIR < 0 }) then {
			for "_b" from 0 to 350 step 30 do {
				if (HMT_AZ_CLAIR < 0) then {
					private _q = _p getPos [HMT_D, _b];
					if (!surfaceIsWater _q) then {
						private _n = [_p, _b] call HMT_fnc_profil;
						if ((_n select 0) == 5) then { HMT_SITE_CLAIR = _p; HMT_AZ_CLAIR = _b };
					};
				};
			};
		};
	};
};

// --- SITE MASQUE : le premier site gele, DEJA CARACTERISE.
// Ma premiere recherche exigeait ZERO ligne-couvert parmi les cinq. C'etait une faute :
// un meme ficus rend MASQUE ou COUVERT selon que la ligne traverse son feuillage ou son
// tronc — mesure du 30/08, 3 masque / 2 couvert / 6 libres sur onze lignes de 80 m.
// Exiger zero couvert, c'est rejeter toute vegetation reelle. On prend donc ce site,
// connu vegetalise, et on RELEVE son profil au lieu de le decreter.
HMT_SITE_MASQ = [8126.45, 10395.4, 0];
HMT_AZ_MASQ   = 310;
HMT_PROFIL_MASQ = [HMT_SITE_MASQ, HMT_AZ_MASQ] call HMT_fnc_profil;
HMT_MASQ_N = HMT_PROFIL_MASQ select 1;
diag_log format ["[R2B] PROFIL du site masque (libre/masque/couvert/terrain) = %1", HMT_PROFIL_MASQ];

diag_log format ["[R2B] SITE CLAIR site=%1 az=%2", HMT_SITE_CLAIR, HMT_AZ_CLAIR];
diag_log format ["[R2B] SITE MASQUE site=%1 az=%2 lignes_masquees=%3/5", HMT_SITE_MASQ, HMT_AZ_MASQ, HMT_MASQ_N];

// ---------------------------------------------------------------------
// COMPTEURS
// ---------------------------------------------------------------------
HMT_obsVu = [0,0,0,0]; HMT_obsNon = [0,0,0,0];
HMT_mortVu = [0,0,0,0]; HMT_mortNon = [0,0,0,0]; HMT_tirsDef = 0;

HMT_fnc_episode = {
	params ["_bras", "_idx"];
	private _masq = (_bras isEqualTo "MASQUE");
	private _cA = if (_masq) then { +HMT_SITE_MASQ } else { +HMT_SITE_CLAIR };
	private _az = if (_masq) then { HMT_AZ_MASQ } else { HMT_AZ_CLAIR };
	private _cD = _cA getPos [HMT_D, _az]; _cD set [2, 0];
	private _props = [];

	// le COUVERT se pose ; le MASQUE est deja la, dans le terrain.
	if (_bras in ["COUVERT", "AVEUGLE"]) then {
		for "_i" from 0 to 23 do {
			private _base = _cA getPos [45 + random 70, _az];
			private _p = [_base, (random 44) - 22, _az] call HMT_fnc_off;
			private _o = createVehicle ["Land_BagFence_Long_F", _p, [], 0, "CAN_COLLIDE"];
			_o setDir (_az + (random 60) - 30);
			_o setPosATL [_p select 0, _p select 1, 0];
			_props pushBack _o;
		};
	};

	private _gd = createGroup east; private _def = [];
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
	if (_bras isEqualTo "AVEUGLE") then {
		{ _x disableAI "AUTOTARGET"; _x disableAI "TARGET"; _x setCombatMode "BLUE"; } forEach _def;
		_gd setCombatMode "BLUE";
	};

	private _ga = createGroup west; private _att = [];
	for "_i" from 0 to (HMT_A - 1) do {
		private _p = [_cA, (_i - 3.5) * 6, _az] call HMT_fnc_off;
		private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
		_u setPosATL [_p select 0, _p select 1, 0];
		_u setSkill 0.55;
		_u setVariable ["hmt_def", _def];
		// ⭐ LA MORT S'ETIQUETTE A L'INSTANT DU COUP FATAL, plus par imputation a 1 Hz.
		_u addEventHandler ["Killed", {
			params ["_mort"];
			private _dd = _mort getVariable ["hmt_def", []];
			private _vu = false; private _dmin = 1e6;
			{
				if (alive _x) then {
					private _q = _x distance2D _mort;
					if (_q < _dmin) then { _dmin = _q };
					if (!_vu && { [_x, _mort] call HMT_fnc_vue }) then { _vu = true };
				};
			} forEach _dd;
			private _k = [_dmin] call HMT_fnc_tranche;
			if (_vu) then { HMT_mortVu set [_k, (HMT_mortVu select _k) + 1] }
			     else { HMT_mortNon set [_k, (HMT_mortNon select _k) + 1] };
		}];
		_att pushBack _u;
	};
	_ga setBehaviour "COMBAT"; _ga setCombatMode "RED"; _ga setSpeedMode "NORMAL";
	{ _x doMove _cD } forEach _att;

	sleep 3;
	private _t0 = time;
	while { time - _t0 < HMT_T } do {
		{
			if (alive _x) then {
				private _cible = _x;
				private _vu = false; private _dmin = 1e6;
				{
					if (alive _x) then {
						private _q = _x distance2D _cible;
						if (_q < _dmin) then { _dmin = _q };
						if (!_vu && { [_x, _cible] call HMT_fnc_vue }) then { _vu = true };
					};
				} forEach _def;
				private _k = [_dmin] call HMT_fnc_tranche;
				if (_vu) then { HMT_obsVu set [_k, (HMT_obsVu select _k) + 1] }
				     else { HMT_obsNon set [_k, (HMT_obsNon select _k) + 1] };
			};
		} forEach _att;
		if (({ alive _x } count _att) == 0) exitWith {};
		sleep 1;
	};

	diag_log format ["[R2B] bras=%1 ep=%2 vivants=%3/%4 obsVu=%5 obsNon=%6 mortVu=%7 mortNon=%8 tirs=%9",
		_bras, _idx, ({ alive _x } count _att), HMT_A, HMT_obsVu, HMT_obsNon, HMT_mortVu, HMT_mortNon, HMT_tirsDef];
	{ if (!isNull _x) then { deleteVehicle _x } } forEach (_att + _def + _props);
	deleteGroup _ga; deleteGroup _gd;
};

[] spawn {
	sleep 5;
	if (HMT_AZ_CLAIR < 0) exitWith { diag_log "[R2B] PAS DE SITE CLAIR — banc arrete" };
	if ((HMT_PROFIL_MASQ select 3) > 0) exitWith {
		diag_log format ["[R2B] SITE MASQUE MASQUE PAR LE TERRAIN (%1) — banc arrete", HMT_PROFIL_MASQ] };
	diag_log format ["[R2B] DEBUT bras=%1 n=%2", HMT_BRAS, HMT_NBRAS];
	{
		private _bras = _x; private _nb = HMT_NBRAS select _forEachIndex;
		HMT_obsVu = [0,0,0,0]; HMT_obsNon = [0,0,0,0];
		HMT_mortVu = [0,0,0,0]; HMT_mortNon = [0,0,0,0]; HMT_tirsDef = 0;
		for "_i" from 0 to (_nb - 1) do { [_bras, _i] call HMT_fnc_episode; sleep 2; };
		{
			private _k = _forEachIndex;
			diag_log format ["[R2B] RESULTAT bras=%1 tranche=<%2 obsVu=%3 mortVu=%4 obsNon=%5 mortNon=%6 tirs=%7",
				_bras, _x, HMT_obsVu select _k, HMT_mortVu select _k,
				HMT_obsNon select _k, HMT_mortNon select _k, HMT_tirsDef];
		} forEach HMT_TRANCHES;
	} forEach HMT_BRAS;
	diag_log "[R2B] FIN";
};
