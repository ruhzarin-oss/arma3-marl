// =====================================================================
// SILENCE RADIO - construction du monde (serveur / solo)
// Le mission.sqm ne contient que le joueur : tout le reste est bati ici,
// pour que le terrain decide ou les choses se posent, pas moi.
// =====================================================================

HMT_ready    = false;
HMT_alarm    = false;
HMT_detected = false;
HMT_props    = [];
HMT_missing  = [];

// --- ancre : outpost sud d'Altis, coordonnees reelles ----------------
HMT_anchor = [8291.45, 10065.42, 0];

0 setOvercast 0;
0 setFog 0;
forceWeatherChange;

// ---------------------------------------------------------------------
// 0. Garde-fou : ne jamais poser une classe qui n'existe pas
// ---------------------------------------------------------------------
HMT_fnc_has = {
	params ["_cls"];
	isClass (configFile >> "CfgVehicles" >> _cls)
};

// ---------------------------------------------------------------------
// 1. Trouver un replat : on echantillonne autour de l'ancre et on garde
//    le point le plus plat, hors eau, loin des maisons.
// ---------------------------------------------------------------------
HMT_fnc_flat = {
	params ["_center", "_radius"];
	private _best = +_center;
	private _bestScore = 1e9;
	for "_i" from 1 to 240 do {
		private _p = _center getPos [sqrt(random 1) * _radius, random 360];
		if (!surfaceIsWater _p) then {
			private _h = getTerrainHeightASL _p;
			private _dev = 0;
			for "_k" from 0 to 7 do {
				private _q = _p getPos [18, _k * 45];
				_dev = _dev max (abs ((getTerrainHeightASL _q) - _h));
			};
			private _pen = count (nearestObjects [_p, ["House"], 45]);
			private _score = _dev + _pen * 4;
			if (_score < _bestScore) then { _bestScore = _score; _best = _p; };
		};
	};
	_best
};

// distance a la mer sur un azimut donne (-1 si pas de mer trouvee)
HMT_fnc_seaDist = {
	params ["_from", "_bearing"];
	private _d = 100;
	private _hit = -1;
	while { _d < 3000 && _hit < 0 } do {
		if (surfaceIsWater (_from getPos [_d, _bearing])) then { _hit = _d };
		_d = _d + 40;
	};
	_hit
};

HMT_camp = [HMT_anchor, 90] call HMT_fnc_flat;
HMT_camp set [2, 0];

// ---------------------------------------------------------------------
// 2. Trouver la cote : l'azimut dont la mer tombe le plus pres de 1100 m
// ---------------------------------------------------------------------
private _bestB = -1;
private _bestErr = 1e9;
private _bestD = 0;
for "_b" from 0 to 350 step 10 do {
	private _d = [HMT_camp, _b] call HMT_fnc_seaDist;
	if (_d > 0) then {
		private _err = abs (_d - 1100);
		if (_err < _bestErr) then { _bestErr = _err; _bestB = _b; _bestD = _d; };
	};
};
if (_bestB < 0) then { _bestB = 180; _bestD = 900; };

HMT_bearing = _bestB;
HMT_insert  = HMT_camp getPos [(_bestD - 45) max 250, _bestB];
HMT_insert set [2, 0];

// exfil : une AUTRE plage, assez loin du camp et de la mise a terre.
// Si le terrain n'en offre pas, on ressort par ou on est entre.
HMT_exfil = +HMT_insert;
private _bestScore = -1;
for "_b" from 0 to 350 step 10 do {
	private _d = [HMT_camp, _b] call HMT_fnc_seaDist;
	if (_d >= 800) then {
		private _p = HMT_camp getPos [_d - 45, _b];
		if (!surfaceIsWater _p && { (_p distance2D HMT_insert) > 500 }) then {
			// on prefere une plage a 90-150 deg de l'axe d'entree
			private _da = abs (((_b - HMT_bearing + 540) mod 360) - 180);
			private _score = 200 - (abs (_da - 110));
			if (_score > _bestScore) then { _bestScore = _score; HMT_exfil = _p; };
		};
	};
};
HMT_exfil set [2, 0];

diag_log format ["[SILENCE RADIO] camp=%1 alt=%2 insert=%3 exfil=%4 az_mer=%5 d_mer=%6",
	HMT_camp, round (getTerrainHeightASL HMT_camp), HMT_insert, HMT_exfil, _bestB, _bestD];

// ---------------------------------------------------------------------
// 3. Le camp
// ---------------------------------------------------------------------
HMT_fnc_prop = {
	params ["_cls", "_dx", "_dy", "_dir"];
	if (!([_cls] call HMT_fnc_has)) exitWith {
		HMT_missing pushBackUnique _cls;
		diag_log format ["[SILENCE RADIO] classe absente, ignoree : %1", _cls];
		objNull
	};
	private _p = [(HMT_camp select 0) + _dx, (HMT_camp select 1) + _dy, 0];
	private _o = createVehicle [_cls, _p, [], 0, "CAN_COLLIDE"];
	_o setDir _dir;
	_o setPosATL [_p select 0, _p select 1, 0];
	HMT_props pushBack _o;
	_o
};

HMT_hq    = ["Land_Cargo_HQ_V1_F",           0,   0,  35] call HMT_fnc_prop;
HMT_radar = ["Land_Radar_Small_F",          16,  12,   0] call HMT_fnc_prop;
HMT_gen   = ["Land_PortableGenerator_01_F", -9,   5, 120] call HMT_fnc_prop;
["Land_Cargo_House_V1_F",  -16,  -8,  35] call HMT_fnc_prop;
["Land_Cargo_House_V1_F",   14, -16,  35] call HMT_fnc_prop;
["Land_Cargo_Patrol_V1_F",  -4,  20, 200] call HMT_fnc_prop;

// mur de HESCO : partiel, avec des trouees. C'est par la que vous entrez.
for "_i" from 0 to 13 do {
	private _a = 20 + _i * 22;
	private _r = 26;
	["Land_HBarrier_Big_F", _r * sin _a, _r * cos _a, _a + 90] call HMT_fnc_prop;
};

// postes de combat
{
	_x params ["_bx", "_by", "_bd"];
	["Land_BagBunker_Small_F", _bx, _by, _bd] call HMT_fnc_prop;
} forEach [[22, 4, 90], [-6, 24, 0], [10, -24, 180]];

// eclairage : ce qui vous trahira, et ce que vous pouvez eteindre
["Land_LampHalogen_F",   8,  10, 210] call HMT_fnc_prop;
["Land_LampHalogen_F", -12,  -2,  60] call HMT_fnc_prop;
["Land_LampHalogen_F",  18,  -6, 300] call HMT_fnc_prop;

// l'objectif "donnees", pose dehors sous les projecteurs
["Land_CampingTable_F", 9.0, -9.6, 215] call HMT_fnc_prop;
HMT_laptop = ["Land_Laptop_unfolded_F", 9.0, -9.0, 215] call HMT_fnc_prop;

// vehicules
{
	_x params ["_cls", "_dist", "_az"];
	if ([_cls] call HMT_fnc_has) then {
		private _v = createVehicle [_cls, HMT_camp getPos [_dist, _az], [], 0, "NONE"];
		_v setDir (random 360);
		_v lock 3;
	};
} forEach [["O_MRAP_02_hmg_F", 34, 250], ["O_Truck_02_covered_F", 30, 300]];

// ---------------------------------------------------------------------
// 4. La garnison
// ---------------------------------------------------------------------
HMT_fnc_kitOpfor = {
	params ["_u"];
	_u linkItem "NVGoggles_OPFOR";
	_u setSkill ["spotDistance",   0.55];
	_u setSkill ["spotTime",       0.55];
	_u setSkill ["aimingAccuracy", 0.35];
	_u setSkill ["courage",        0.80];
};

// -- garde rapprochee : elle vit dans le camp, elle n'est pas figee
HMT_grpCamp = createGroup east;
{
	private _u = HMT_grpCamp createUnit [_x, HMT_camp getPos [12 + random 14, random 360], [], 0, "NONE"];
	[_u] call HMT_fnc_kitOpfor;
} forEach ["O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_F","O_medic_F","O_Soldier_M_F"];
HMT_grpCamp setBehaviour "SAFE";
HMT_grpCamp setCombatMode "YELLOW";
HMT_grpCamp setSpeedMode "LIMITED";
[HMT_grpCamp, HMT_camp, 45] call BIS_fnc_taskPatrol;

// -- patrouille exterieure : c'est elle qui vous coupe la route
HMT_grpPat = createGroup east;
{
	private _u = HMT_grpPat createUnit [_x, HMT_camp getPos [200, HMT_bearing], [], 0, "NONE"];
	[_u] call HMT_fnc_kitOpfor;
} forEach ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_LAT_F","O_Sharpshooter_F"];
HMT_grpPat setBehaviour "SAFE";
HMT_grpPat setCombatMode "YELLOW";
HMT_grpPat setSpeedMode "LIMITED";
[HMT_grpPat, HMT_camp, 280] call BIS_fnc_taskPatrol;

// -- deux mitrailleuses servies
HMT_grpHmg = createGroup east;
{
	_x params ["_hx", "_hy", "_hd"];
	private _p = [(HMT_camp select 0) + _hx, (HMT_camp select 1) + _hy, 0];
	private _s = createVehicle ["O_HMG_01_high_F", _p, [], 0, "CAN_COLLIDE"];
	_s setDir _hd;
	private _g = HMT_grpHmg createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
	[_g] call HMT_fnc_kitOpfor;
	_g moveInGunner _s;
} forEach [[24, 6, 100], [-8, 26, 350]];
HMT_grpHmg setBehaviour "SAFE";
HMT_grpHmg setCombatMode "YELLOW";

// -- QRF : dort a 1,2 km, ne bouge que si l'alarme part
HMT_qrfPos = HMT_camp getPos [1200, HMT_bearing + 180];
HMT_grpQrf = createGroup east;
{
	private _u = HMT_grpQrf createUnit [_x, HMT_qrfPos, [], 0, "NONE"];
	[_u] call HMT_fnc_kitOpfor;
} forEach ["O_Soldier_SL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_F","O_Soldier_LAT_F","O_medic_F"];
HMT_grpQrf setBehaviour "SAFE";
HMT_grpQrf setCombatMode "YELLOW";
private _wq = HMT_grpQrf addWaypoint [HMT_qrfPos, 0];
_wq setWaypointType "HOLD";

// ---------------------------------------------------------------------
// 5. Marqueurs
// ---------------------------------------------------------------------
private _m = createMarker ["mrk_obj", HMT_camp];
_m setMarkerShape "ICON";
_m setMarkerType "o_installation";
_m setMarkerColor "ColorOPFOR";
_m setMarkerText "Relais Kappa";

private _m2 = createMarker ["mrk_exfil", HMT_exfil];
_m2 setMarkerShape "ICON";
_m2 setMarkerType "mil_pickup";
_m2 setMarkerColor "ColorBLUFOR";
_m2 setMarkerText "Exfiltration";
_m2 setMarkerAlpha 0;

private _m3 = createMarker ["mrk_zone", HMT_camp];
_m3 setMarkerShape "ELLIPSE";
_m3 setMarkerBrush "Border";
_m3 setMarkerSize [300, 300];
_m3 setMarkerColor "ColorRed";
_m3 setMarkerAlpha 0.45;

private _m4 = createMarker ["mrk_insert", HMT_insert];
_m4 setMarkerShape "ICON";
_m4 setMarkerType "mil_start";
_m4 setMarkerColor "ColorBLUFOR";
_m4 setMarkerText "Mise a terre";

// ---------------------------------------------------------------------
// 6. Taches
// ---------------------------------------------------------------------
[west, "tIntel", ["Un terminal tourne encore dans le camp. Copiez son contenu AVANT de faire sauter l'antenne.", "Copier les donnees", "mrk_obj"], HMT_camp, "CREATED", 10, true, "documents"] call BIS_fnc_taskCreate;
[west, "tRadar", ["Detruisez l'antenne du relais. Une charge explosive suffit ; un tir d'arme legere ne suffira pas.", "Faire taire le relais", "mrk_obj"], HMT_camp, "CREATED", 9, true, "destroy"] call BIS_fnc_taskCreate;

// ---------------------------------------------------------------------
// 7. L'alarme : elle est de camp, pas de soldat, et elle ne retombe pas
// ---------------------------------------------------------------------
[] spawn {
	waitUntil { sleep 1; !isNull player };
	while { !HMT_alarm } do {
		sleep 1.5;
		if ((east knowsAbout player) > 1.5) then { HMT_alarm = true };
	};

	HMT_detected = true;

	[] spawn {
		for "_i" from 1 to 6 do {
			private _p = HMT_camp getPos [random 60, random 360];
			createVehicle ["F_40mm_White", [_p select 0, _p select 1, 150], [], 0, "CAN_COLLIDE"];
			sleep 22;
		};
	};

	{
		_x setBehaviour "COMBAT";
		_x setCombatMode "RED";
		_x setSpeedMode "FULL";
	} forEach [HMT_grpCamp, HMT_grpPat, HMT_grpHmg, HMT_grpQrf];

	while { count (waypoints HMT_grpQrf) > 0 } do {
		deleteWaypoint ((waypoints HMT_grpQrf) select 0);
	};
	private _w = HMT_grpQrf addWaypoint [HMT_camp, 0];
	_w setWaypointType "SAD";
	_w setWaypointSpeed "FULL";
	_w setWaypointBehaviour "AWARE";

	"ALERTE - le camp vous a reperes. Une reaction arrive du nord." remoteExec ["hint", 0];
};

// ---------------------------------------------------------------------
// 8. Suivi de l'antenne
// ---------------------------------------------------------------------
[] spawn {
	if (isNull HMT_radar) exitWith {
		HMT_radarDown = true;
		["tRadar", "SUCCEEDED"] call BIS_fnc_taskSetState;
	};
	waitUntil { sleep 2; !alive HMT_radar || { damage HMT_radar > 0.6 } };
	["tRadar", "SUCCEEDED"] call BIS_fnc_taskSetState;
	HMT_radarDown = true;
};

if (count HMT_missing > 0) then {
	diag_log format ["[SILENCE RADIO] ATTENTION classes absentes : %1", HMT_missing];
};

HMT_ready = true;
publicVariable "HMT_ready";
diag_log "[SILENCE RADIO] monde pret";
