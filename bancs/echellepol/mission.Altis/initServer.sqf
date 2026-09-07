// =====================================================================
// ECHELLE — LE BANC AVEC LE TEMOIN `POLITIQUE`
//
// La mission CONDUIT : elle monte la scene, decide de la prise, de la mort, du timeout,
// et nettoie. Python SERT : il recoit neuf nombres, il rend un entier de 0 a 12.
// Rien d'autre ne traverse la frontiere.
//
// L'ALEA DU MONDE EST TIRE COTE PYTHON et voyage dans le TICKET — le `random` de SQF ne
// se graine pas, donc « graines neuves » ne serait ni vrai ni rejouable autrement.
//
// PONT : entree par la DLL `hmt_ext` (lecture au niveau OS, pas de gel d'index),
// sortie par `diag_log`. Latence mesuree : mediane 0,516 s, p99 0,566 s, 0 perte sur 100.
//
// ⚠️ L'actuateur exige les commandes DANS L'ORDRE. La mission publie `HMT_SYNC` pour que
// Python se cale : sans ca les deux cotes s'attendent, et cette attente est indiscernable
// d'un pont mort. C'est arrive.
// =====================================================================

HMT_RAYON_K = 0.10; HMT_RAYON_MIN = 6;      // rayon = 10 % de D, plancher 6 m
HMT_T_K     = 0.50; HMT_T_MIN     = 20;     // budget = 0,5 s par metre, plancher 20 s
HMT_CYCLE   = 4;                            // un geste toutes les 4 s
HMT_NGESTES = 13;
HMT_PATIENCE = 2.5;                         // attente maximale d'un geste, secondes

HMT_n = 0; HMT_ACT = []; HMT_TICKET = []; HMT_STOP = false; HMT_ETAT = "DEMARRAGE";
0 setOvercast 0; 0 setFog 0; forceWeatherChange;
enableSaving [false, false];

// ---------------------------------------------------------------------
// ACTUATEUR — il ne fait qu'executer ce que Python ecrit
// ---------------------------------------------------------------------
[] spawn {
	while { !HMT_STOP } do {
		private _next = HMT_n + 1;
		private _code = "hmt_ext" callExtension (str _next);
		if !(_code isEqualTo "") then { HMT_n = _next; call compile _code; };
		sleep 0.1;
	};
};
[] spawn {
	// ⚠️ L'ETAT SE REPETE. Un « PRET » dit une seule fois, c'est un etat qu'on rate :
		// Python ouvre le RPT a la fin et ne voit pas ce qui precede. Le battement porte
		// donc le compteur ET l'etat, toutes les 2 s.
		while { !HMT_STOP } do { diag_log format ["[ECHP] HMT_SYNC %1 ETAT %2", HMT_n, HMT_ETAT]; sleep 2; };
};

// ---------------------------------------------------------------------
// LE TERRAIN GELE — recherche deterministe, identique au banc des temoins
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
					  for "_k" from 0 to 3 do { _dev = _dev max (abs ((getTerrainHeightASL (_x getPos [14, _k * 90])) - _h)) };
					} forEach [_p, _q];
					private _s = _m - _dev * 0.4;
					if (_s > _meilleur) then { _meilleur = _s; HMT_SITE = _p; HMT_AZ = _b; };
				};
			};
		};
	};
};
HMT_SITE set [2, 0];
diag_log format ["[ECHP] SITE %1 az=%2 degagement=%3", HMT_SITE, HMT_AZ, (_meilleur toFixed 2)];

// ---------------------------------------------------------------------
// LE CATALOGUE — 13 gestes, interface constante sur toute l'echelle
// ---------------------------------------------------------------------
HMT_fnc_geste = {
	params ["_u", "_g", "_obj", "_enn"];
	if (!alive _u) exitWith { false };
	private _fait = true;
	switch (true) do {
		case (_g < 8): { _u doMove (_u getPos [40, _g * 45]) };
		case (_g == 8): {
			private _d = _u distance2D _obj;
			_u doMove (if (_d < 45) then { _obj } else { _u getPos [40, _u getDir _obj] });
		};
		case (_g == 9): {
			// ENGAGER : designer UNE fois, laisser l'IA native tirer. Micro-gerer le feu
			// reinitialise la visee — mesure du 09/07, on ne la refait pas.
			// Depuis le 03/09 ce geste LEVE AUSSI LA SECURITE : le groupe est en BLUE par
			// defaut, ENGAGER est la seule facon d'ouvrir le feu.
			if (!isNull _enn && { alive _enn }) then {
				_u setCombatMode "RED";
				_u reveal [_enn, 4]; _u doTarget _enn; _u doFire _enn;
			}
			else { _fait = false };   // geste impossible : AVOUE, jamais masque
		};
		case (_g == 10): { _u setUnitPos "UP" };
		case (_g == 11): { _u setUnitPos "MIDDLE" };
		default          { _u setUnitPos "DOWN" };
	};
	_fait
};

// ---------------------------------------------------------------------
// LES NEUF NOMBRES — repere MONDE, parce que les gestes sont des caps ABSOLUS
// ---------------------------------------------------------------------
HMT_fnc_obs = {
	params ["_u", "_obj", "_ennemis", "_D"];
	private _po = getPosATL _u;
	private _vx = (_obj select 0) - (_po select 0);
	private _vy = (_obj select 1) - (_po select 1);
	private _d  = sqrt (_vx * _vx + _vy * _vy);
	private _ux = if (_d > 0.1) then { _vx / _d } else { 0 };
	private _uy = if (_d > 0.1) then { _vy / _d } else { 0 };

	private _vivants = _ennemis select { alive _x };
	private _de = 2.0; private _ex = 0; private _ey = 0;
	if (count _vivants > 0) then {
		private _best = objNull; private _bd = 1e9;
		{ private _q = _u distance2D _x; if (_q < _bd) then { _bd = _q; _best = _x } } forEach _vivants;
		_de = (_bd / 200) min 2.0;
		private _pe = getPosATL _best;
		private _wx = (_pe select 0) - (_po select 0);
		private _wy = (_pe select 1) - (_po select 1);
		if (_bd > 0.1) then { _ex = _wx / _bd; _ey = _wy / _bd };
	};
	private _post = switch (unitPos _u) do { case "DOWN": {1}; case "MIDDLE": {0.5}; default {0} };
	[ (_d / _D) min 2.0, _ux, _uy, _de, _ex, _ey, (count _vivants) / 8, _post, getSuppression _u ]
};

// ---------------------------------------------------------------------
// UN EPISODE, CONDUIT PAR LA MISSION
// ---------------------------------------------------------------------
HMT_fnc_episode = {
	params ["_uid", "_barreau", "_D", "_dx", "_dy", "_daz", ["_sx", -1], ["_sy", -1], ["_saz", -1], ["_capDef", 0]];
	// ⚠️ _capDef : le cap du defenseur, RELATIF a l'axe d'approche.
	//   0   = il vous fait face                180 = il vous tourne le dos
	// La geometrie du cone devient ainsi une variable TIREE COTE PYTHON et rejouable,
	// au lieu d'etre subie. C'est elle que le canal « cone » devra predire, et c'est le
	// banc de l'angle mort (18/18 dans le cone, 0/26 hors) qui sert de verite de terrain.
	private _rayon = HMT_RAYON_MIN max (_D * HMT_RAYON_K);
	private _T     = HMT_T_MIN max (_D * HMT_T_K);
	private _site  = if (_sx < 0) then { HMT_SITE } else { [_sx, _sy, 0] };
	private _azb   = if (_sx < 0) then { HMT_AZ }   else { _saz };
	private _az    = _azb + _daz;
	private _p0    = [(_site select 0) + _dx, (_site select 1) + _dy, 0];
	diag_log format ["[ECHP] SITEUSE %1 %2 %3 %4", _uid, (_site select 0) toFixed 2, (_site select 1) toFixed 2, _azb];
	private _obj   = _p0 getPos [_D, _az]; _obj set [2, 0];

	private _ga = createGroup west;
	private _u = _ga createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
	_u setPosATL [_p0 select 0, _p0 select 1, 0];
	_u setDir _az; _u setSkill 0.6; _u setUnitPos "UP";
	_ga setBehaviour "AWARE"; _ga setCombatMode "BLUE";
	// ⚠️ BLUE = ne tire JAMAIS de lui-meme. Mesure du 03/09 : en YELLOW l'agent abattait
	// le defenseur en 118 coups sur 20 episodes, avant meme d'avoir a le lire. Un agent
	// arme n'a pas besoin de percevoir une menace, il la tue.
	// On ne le DESARME pas pour autant : ENGAGER doit rester un geste qui fait quelque
	// chose, sinon c'est un geste nul dans le catalogue — et un geste nul fait
	// s'effondrer une politique. C'est ENGAGER qui leve la securite, lui seul.
	HMT_coups = 0;
	_u addEventHandler ["Fired", { HMT_coups = HMT_coups + 1 }];

	private _enn = objNull; private _gd = grpNull; private _ennemis = [];
	if (_barreau in ["B1", "B1i"]) then {
		// ⚠️ LE DEFENSEUR N'EST PLUS SUR L'OBJECTIF. Mesure du 03/09 : place dessus, il
		// rendait la doctrine a 0/51 — reussir exigeait d'arriver a 6 m de lui, donc la
		// tache etait « marcher dans le canon » et aucune lecture de cone n'en sauvait.
		// Il se tient desormais 40 m AU-DELA de l'objectif, sur l'axe d'approche : l'agent
		// traverse 30 m vers un point situe a 40 m devant lui, et c'est le CAP du
		// defenseur qui decide s'il est vu. La geometrie redevient la question.
		private _pDef = _obj getPos [40, _az];
		_gd = createGroup east;
		_enn = _gd createUnit ["O_Soldier_F", _pDef, [], 0, "NONE"];
		_enn setPosATL [_pDef select 0, _pDef select 1, 0];
		// ⚠️ SEUL « PATH » RESTE COUPE : le defenseur ne se deplace pas, son cap est
		// verrouille, et la geometrie du cone reste donc celle que le ticket a decidee.
		// Tout le reste de son IA est RENDU : il voit, il choisit, il tire.
		_enn disableAI "PATH";
		_enn setBehaviour "AWARE"; _enn setCombatMode "RED"; _enn setUnitPos "UP";
		_gd setBehaviour "AWARE"; _gd setCombatMode "RED";
		// ⚠️ `setDir` SEUL NE TIENT PAS : mesure du 03/09, un cap pose a 90 bascule a 3,6
		// en deux secondes. `doWatch` sur un point lointain le verrouille — verifie sur
		// 16 s. Sans ca la variable « cone » du ticket serait une fiction.
		private _capAbs = (_az + 180 + _capDef) % 360;
		_enn setDir _capAbs;
		_enn setFormDir _capAbs;
		_enn doWatch (_pDef getPos [400, _capAbs]);
		_enn setSkill 0.6;
		diag_log format ["[ECHP] DEFENSEUR %1 pose=%2 relatif=%3 dist_obj=%4",
			_uid, _capAbs toFixed 1, _capDef toFixed 1, (_enn distance2D _obj) toFixed 1];
		_ennemis = [_enn];
	};

	sleep 1.5;
	private _t0 = time; private _prise = 0; private _cycle = 0;
	private _voids = 0; private _refus = 0;

	while { time - _t0 < _T && _prise == 0 && alive _u && _voids == 0 } do {
		private _o = [_u, _obj, _ennemis, _D] call HMT_fnc_obs;
		diag_log format ["[ECHP] OBS %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 %11",
			_uid, _cycle,
			((_o select 0) toFixed 4), ((_o select 1) toFixed 4), ((_o select 2) toFixed 4),
			((_o select 3) toFixed 4), ((_o select 4) toFixed 4), ((_o select 5) toFixed 4),
			((_o select 6) toFixed 4), ((_o select 7) toFixed 4), ((_o select 8) toFixed 4)];

		// attente BORNEE du geste. Un geste absent ou perime rend l'episode VOID :
		// jamais compte, cause journalisee. Un pont mort ne doit pas fabriquer des echecs.
		private _tA = time; private _g = -1;
		while { time - _tA < HMT_PATIENCE && _g < 0 } do {
			if (count HMT_ACT == 3) then {
				if ((HMT_ACT select 0) == _uid && { (HMT_ACT select 1) == _cycle }) then {
					_g = HMT_ACT select 2; HMT_ACT = [];
				};
			};
			if (_g < 0) then { sleep 0.05 };
		};
		if (_g < 0) then { _voids = 1 }
		else {
			private _fait = [_u, _g, _obj, _enn] call HMT_fnc_geste;
			if (!_fait) then { _refus = _refus + 1 };
			diag_log format ["[ECHP] ACT %1 %2 %3 %4", _uid, _cycle, _g, if (_fait) then {1} else {0}];
			private _k = 0;
			while { _k < HMT_CYCLE && _prise == 0 && alive _u } do {
				sleep 0.5; _k = _k + 0.5;
				private _arrive = (_u distance2D _obj) < _rayon;
				// ⚠️ DEUX BARREAUX DISTINCTS, UNE QUESTION CHACUN.
				//   B1i (infiltration) : ARRIVER VIVANT sous surveillance. C'est
				//     « lit-il la menace et la contourne-t-il ».
				//   B1  (combat)       : arriver ET avoir neutralise. C'est
				//     « tire-t-il le premier », et c'est un barreau a lui seul.
				// Le 03/09, B1 rendait 0/51 : la doctrine ne tire pas (combatMode BLUE
				// depuis le point 2), donc le defenseur ne mourait jamais et la prise
				// etait impossible PAR CONSTRUCTION — 34 agents sur 51 etaient pourtant
				// arrives, distance mediane au but 1 m.
				if (_barreau isEqualTo "B1") then { if (_arrive && { !alive _enn }) then { _prise = 1 } }
				else { if (_arrive) then { _prise = 1 } };
			};
			_cycle = _cycle + 1;
		};
	};

	private _dfin = round (_u distance2D _obj);
	private _viv  = if (alive _u) then { 1 } else { 0 };
	diag_log format ["[ECHP] RESULT %1 %2 %3 %4 %5 %6 %7 %8",
		_uid, _prise, ((time - _t0) toFixed 1), _dfin, _viv, HMT_coups, _voids, _refus];

	{ if (!isNull _x) then { deleteVehicle _x } } forEach [_u, _enn];
	deleteGroup _ga; if (!isNull _gd) then { deleteGroup _gd };
};

// ---------------------------------------------------------------------
// BOUCLE PRINCIPALE — elle attend un ticket, joue, et redevient disponible
// ---------------------------------------------------------------------
[] spawn {
	sleep 4;
	HMT_ETAT = "PRET";
	while { !HMT_STOP } do {
		if ((count HMT_TICKET) in [6, 9, 10]) then {
			private _t = +HMT_TICKET; HMT_TICKET = [];
			HMT_ETAT = "OCCUPE";
			_t call HMT_fnc_episode;
			HMT_ETAT = "PRET";
		};
		sleep 0.1;
	};
};
