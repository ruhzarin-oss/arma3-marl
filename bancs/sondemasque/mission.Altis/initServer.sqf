// =====================================================================
// REPRODUCTION EXACTE — le ficus du 30/08, puis balayage fin autour
// Ma sonde precedente n'a rien trouve sur 105 lignes, alors qu'une ligne de ce site
// etait COUPEE par un ficus il y a une heure. Avant de conclure quoi que ce soit sur
// la vegetation d'Arma, je reproduis la geometrie EXACTE qui avait mordu.
// =====================================================================
0 setOvercast 0; 0 setFog 0; forceWeatherChange;

HMT_fnc_cl = {
	params ["_a", "_b"];
	private _ter = terrainIntersectASL [_a, _b];
	private _sv = lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "VIEW", "VIEW"];
	private _sf = lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "FIRE", "FIRE"];
	private _qui = "aucun";
	if (count _sv > 0) then {
		private _o = (_sv select 0) select 2;
		_qui = if (isNull _o) then { "nul" } else { typeOf _o };
		if (_qui isEqualTo "") then { _qui = str _o };
	};
	[_ter, count _sv, count _sf, _qui]
};

[] spawn {
	sleep 6;
	private _c = [8126.45, 10395.4, 0];
	private _az = 310;

	// 1. LA REPRODUCTION : deux hommes reels, comme le 30/08
	private _pa = _c getPos [30, _az];
	private _pb = _c getPos [30, _az + 180];
	private _ga = createGroup west; private _gb = createGroup east;
	private _a = _ga createUnit ["B_Soldier_F", _pa, [], 0, "NONE"];
	private _b = _gb createUnit ["O_Soldier_F", _pb, [], 0, "NONE"];
	_a setPosATL [_pa select 0, _pa select 1, 0];
	_b setPosATL [_pb select 0, _pb select 1, 0];
	{ _x disableAI "PATH"; _x setUnitPos "UP"; _x allowDamage false } forEach [_a, _b];
	sleep 3;
	private _xa = getPosASL _a; private _xb = getPosASL _b;
	private _ea = [_xa select 0, _xa select 1, (_xa select 2) + 1.5];
	private _eb = [_xb select 0, _xb select 1, (_xb select 2) + 1.0];
	private _r = [_ea, _eb] call HMT_fnc_cl;
	diag_log format ["[MQ3] REPRODUCTION hommes reels : terrain=%1 vue=%2 tir=%3 par %4  (dist=%5)",
		_r select 0, _r select 1, _r select 2, _r select 3, round (_a distance _b)];

	// meme ligne, mais hauteurs prises sur le TERRAIN — c'est ce que faisait la sonde muette
	private _ta = [_xa select 0, _xa select 1, (getTerrainHeightASL _pa) + 1.6];
	private _tb = [_xb select 0, _xb select 1, (getTerrainHeightASL _pb) + 1.6];
	private _r2 = [_ta, _tb] call HMT_fnc_cl;
	diag_log format ["[MQ3] MEME LIGNE, hauteurs terrain+1,6 : terrain=%1 vue=%2 tir=%3 par %4",
		_r2 select 0, _r2 select 1, _r2 select 2, _r2 select 3];

	// 2. QUE Y A-T-IL AUTOUR ? on demande la liste des objets, sans filtre de classe
	private _objs = nearestObjects [_c, [], 60];
	diag_log format ["[MQ3] objets a 60 m : %1", count _objs];
	private _n = 0;
	{
		if (_n < 12) then {
			private _t = typeOf _x;
			diag_log format ["[MQ3]   obj %1 : type='%2' modele=%3 dist=%4",
				_n, _t, str _x, round (_x distance _c)];
			_n = _n + 1;
		};
	} forEach _objs;

	// 3. BALAYAGE FIN a hauteur d'homme reel, autour du centre
	private _masq = 0; private _couv = 0; private _libre = 0;
	for "_lat" from -30 to 30 step 6 do {
		private _p = [(_c select 0) + _lat * sin (_az + 90), (_c select 1) + _lat * cos (_az + 90), 0];
		private _q = _p getPos [80, _az];
		private _h1 = [_p select 0, _p select 1, (getTerrainHeightASL _p) + 1.5];
		private _h2 = [_q select 0, _q select 1, (getTerrainHeightASL _q) + 1.0];
		private _z = [_h1, _h2] call HMT_fnc_cl;
		if (!(_z select 0)) then {
			if ((_z select 1) > 0 && { (_z select 2) == 0 }) then { _masq = _masq + 1;
				diag_log format ["[MQ3] MASQUE lat=%1 par %2", _lat, _z select 3] };
			if ((_z select 1) > 0 && { (_z select 2) > 0 }) then { _couv = _couv + 1;
				diag_log format ["[MQ3] couvert lat=%1 par %2", _lat, _z select 3] };
			if ((_z select 1) == 0) then { _libre = _libre + 1 };
		};
	};
	diag_log format ["[MQ3] BALAYAGE 80 m : masque=%1 couvert=%2 libre=%3", _masq, _couv, _libre];
	{ deleteVehicle _x } forEach [_a, _b];
	diag_log "[MQ3] FIN";
};
