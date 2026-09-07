// =====================================================================
// SERPENT NOIR — infiltration solitaire, neutralisation d'un HVT
// Un homme. Aucun appui. Aucune evacuation. Le camp ne pardonne pas.
// Tout est bati en SQF : le mission.sqm ne contient que le joueur.
// =====================================================================

HMT_ready = false; HMT_alarme = false; HMT_detecte = false;
HMT_props = []; HMT_manquantes = [];
HMT_hvtMort = false; HMT_hvtFui = false; HMT_intel = false;

HMT_ANCRE   = [12479.84, 15197.45, 0];   // outpost du centre d'Altis, coordonnees reelles
HMT_LIMITE  = 2100;                      // secondes avant que la cible parte d'elle-meme

0 setOvercast 0; 0 setFog 0; forceWeatherChange;

HMT_fnc_has = { isClass (configFile >> "CfgVehicles" >> (_this select 0)) };

// ---------------------------------------------------------------------
// 1. LE TERRAIN — replat pour le camp, et un point d'observation qui VOIT
// ---------------------------------------------------------------------
HMT_fnc_plat = {
	params ["_c", "_r"];
	private _best = +_c; private _sc = 1e9;
	for "_i" from 1 to 260 do {
		private _p = _c getPos [sqrt(random 1) * _r, random 360];
		if (!surfaceIsWater _p) then {
			private _h = getTerrainHeightASL _p; private _dev = 0;
			for "_k" from 0 to 7 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [20, _k * 45])) - _h)) };
			private _s = _dev + 5 * (count (nearestObjects [_p, ["House"], 70]));
			if (_s < _sc) then { _sc = _s; _best = _p };
		};
	};
	_best
};
HMT_fnc_libre = {
	params ["_p", "_q"];
	private _a = [_p select 0, _p select 1, (getTerrainHeightASL _p) + 1.6];
	private _b = [_q select 0, _q select 1, (getTerrainHeightASL _q) + 1.6];
	if (terrainIntersectASL [_a, _b]) exitWith { false };
	(count (lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "VIEW", "VIEW"])) == 0
};

HMT_CAMP = [HMT_ANCRE, 110] call HMT_fnc_plat;
HMT_CAMP set [2, 0];

// le point d'observation : haut, a 350-600 m, avec vue franche sur le camp.
// Sans lui la mission n'a pas de phase de renseignement, elle n'a qu'un assaut.
// LE POINT D'OBSERVATION. Premier essai : exiger une ligne de vue TOTALEMENT libre sur
// 350-1500 m. Resultat mesure : le meilleur point trouve etait 34 m EN DESSOUS du camp,
// deux fois de suite. La contrainte etait trop dure — a cette distance un seul buisson
// disqualifie une crete. On prend donc la HAUTEUR d'abord, et on RELEVE ensuite si la vue
// est franche ou non. Le briefing dira ce qui a ete mesure, pas ce qui arrangerait.
HMT_OP = []; HMT_OP_GAIN = -1e9;
for "_i" from 1 to 1200 do {
	private _p = HMT_CAMP getPos [380 + random 620, random 360];
	_p set [2, 0];
	if (!surfaceIsWater _p && { (count (nearestObjects [_p, ["House"], 40])) == 0 }) then {
		private _gain = (getTerrainHeightASL _p) - (getTerrainHeightASL HMT_CAMP);
		if (_gain > HMT_OP_GAIN) then { HMT_OP_GAIN = _gain; HMT_OP = _p };
	};
};
if (count HMT_OP == 0) then { HMT_OP = HMT_CAMP getPos [450, random 360]; HMT_OP set [2,0]; HMT_OP_GAIN = 0 };
HMT_OP_VUE = [HMT_OP, HMT_CAMP] call HMT_fnc_libre;
private _meilleur = HMT_OP_GAIN;
diag_log format ["[SN] point d observation : gain=%1 m vue_franche=%2", round HMT_OP_GAIN, HMT_OP_VUE];

// l'avant-poste du renseignement : entre l'observatoire et le camp, decale
HMT_RELAIS = HMT_CAMP getPos [520, (HMT_CAMP getDir HMT_OP) + 70];
HMT_RELAIS = [HMT_RELAIS, 60] call HMT_fnc_plat;
HMT_RELAIS set [2, 0];

// mise a terre : 1,4 km, hors de tout
HMT_INSERT = HMT_CAMP getPos [1400, (HMT_CAMP getDir HMT_OP) + 25];
HMT_INSERT = [HMT_INSERT, 70] call HMT_fnc_plat;
HMT_INSERT set [2, 0];

// exfiltration : ailleurs, loin, et pas sur le chemin d'entree
HMT_EXFIL = HMT_CAMP getPos [1250, (HMT_CAMP getDir HMT_OP) - 110];
HMT_EXFIL = [HMT_EXFIL, 70] call HMT_fnc_plat;
HMT_EXFIL set [2, 0];

// la route de fuite du HVT : a l'oppose de l'observatoire
HMT_FUITE = HMT_CAMP getPos [1800, (HMT_CAMP getDir HMT_OP) + 180];
HMT_FUITE set [2, 0];

diag_log format ["[SN] camp=%1 alt=%2 op=%3 (+%4 m) relais=%5 insert=%6 exfil=%7",
	HMT_CAMP, round (getTerrainHeightASL HMT_CAMP), HMT_OP, round _meilleur,
	HMT_RELAIS, HMT_INSERT, HMT_EXFIL];

// ---------------------------------------------------------------------
// 2. LE CAMP — mur fermé, tour, projecteurs
// ---------------------------------------------------------------------
HMT_fnc_pose = {
	params ["_cls", "_c", "_dx", "_dy", "_dir"];
	if (!([_cls] call HMT_fnc_has)) exitWith { HMT_manquantes pushBackUnique _cls; objNull };
	private _p = [(_c select 0) + _dx, (_c select 1) + _dy, 0];
	private _o = createVehicle [_cls, _p, [], 0, "CAN_COLLIDE"];
	_o setDir _dir; _o setPosATL [_p select 0, _p select 1, 0];
	HMT_props pushBack _o; _o
};

HMT_QG   = ["Land_Cargo_HQ_V1_F",    HMT_CAMP,   0,   0,  40] call HMT_fnc_pose;
HMT_BAR  = ["Land_Cargo_House_V1_F", HMT_CAMP, -22,  10,  40] call HMT_fnc_pose;
["Land_Cargo_House_V1_F", HMT_CAMP,  20, -18,  40] call HMT_fnc_pose;
HMT_TOUR = ["Land_Cargo_Patrol_V1_F",HMT_CAMP,   6,  24, 200] call HMT_fnc_pose;
// enceinte quasi fermee : deux ouvertures seulement, et il faut les trouver
for "_i" from 0 to 19 do {
	private _a = _i * 18;
	if (!(_a in [126, 144, 288, 306])) then {
		["Land_HBarrier_Big_F", HMT_CAMP, 34 * sin _a, 34 * cos _a, _a + 90] call HMT_fnc_pose;
	};
};
{ _x params ["_bx","_by","_bd"]; ["Land_BagBunker_Small_F", HMT_CAMP, _bx, _by, _bd] call HMT_fnc_pose; }
	forEach [[30,8,95],[-10,31,350],[14,-30,175],[-30,-12,265]];
{ ["Land_LampHalogen_F", HMT_CAMP, _x select 0, _x select 1, _x select 2] call HMT_fnc_pose; }
	forEach [[10,12,210],[-14,-4,60],[22,-10,300],[-6,26,120]];
["Land_CampingTable_F", HMT_CAMP, 11, -11, 215] call HMT_fnc_pose;
HMT_LAPTOP_CAMP = ["Land_Laptop_unfolded_F", HMT_CAMP, 11, -10.4, 215] call HMT_fnc_pose;

// --- l'avant-poste du renseignement, plus leger
{ ["Land_HBarrier_Big_F", HMT_RELAIS, 12 * sin (_x * 60), 12 * cos (_x * 60), _x * 60 + 90] call HMT_fnc_pose; } forEach [0,1,2,4,5];
["Land_Cargo_House_V1_F", HMT_RELAIS, 0, 0, 20] call HMT_fnc_pose;
["Land_LampHalogen_F", HMT_RELAIS, 6, 4, 180] call HMT_fnc_pose;
["Land_CampingTable_F", HMT_RELAIS, -4, 3, 20] call HMT_fnc_pose;
HMT_LAPTOP_RELAIS = ["Land_Laptop_unfolded_F", HMT_RELAIS, -4, 3.6, 20] call HMT_fnc_pose;

// ---------------------------------------------------------------------
// 3. LES HOMMES — et ils sont nombreux
// ---------------------------------------------------------------------
HMT_fnc_kit = {
	params ["_u", ["_skill", 0.6]];
	_u linkItem "NVGoggles_OPFOR";
	_u setSkill ["spotDistance", _skill]; _u setSkill ["spotTime", _skill];
	_u setSkill ["aimingAccuracy", _skill * 0.7]; _u setSkill ["courage", 0.9];
};

// -- garde du camp
HMT_gCamp = createGroup east;
{ private _u = HMT_gCamp createUnit [_x, HMT_CAMP getPos [14 + random 16, random 360], [], 0, "NONE"]; [_u] call HMT_fnc_kit; }
	forEach ["O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_F","O_Soldier_F","O_medic_F","O_Soldier_M_F","O_Soldier_LAT_F"];
HMT_gCamp setBehaviour "SAFE"; HMT_gCamp setCombatMode "YELLOW"; HMT_gCamp setSpeedMode "LIMITED";
[HMT_gCamp, HMT_CAMP, 40] call BIS_fnc_taskPatrol;

// -- deux patrouilles exterieures, rayons differents
HMT_gP1 = createGroup east;
{ private _u = HMT_gP1 createUnit [_x, HMT_CAMP getPos [150, random 360], [], 0, "NONE"]; [_u] call HMT_fnc_kit; }
	forEach ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_LAT_F","O_Sharpshooter_F"];
HMT_gP1 setBehaviour "SAFE"; HMT_gP1 setCombatMode "YELLOW"; HMT_gP1 setSpeedMode "LIMITED";
[HMT_gP1, HMT_CAMP, 200] call BIS_fnc_taskPatrol;

HMT_gP2 = createGroup east;
{ private _u = HMT_gP2 createUnit [_x, HMT_CAMP getPos [380, random 360], [], 0, "NONE"]; [_u] call HMT_fnc_kit; }
	forEach ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_F","O_Soldier_AR_F"];
HMT_gP2 setBehaviour "SAFE"; HMT_gP2 setCombatMode "YELLOW"; HMT_gP2 setSpeedMode "LIMITED";
[HMT_gP2, HMT_CAMP, 450] call BIS_fnc_taskPatrol;

// -- le guetteur de la tour : c'est lui qui voit loin
HMT_gTour = createGroup east;
HMT_guetteur = HMT_gTour createUnit ["O_Sharpshooter_F", HMT_CAMP getPos [26, 20], [], 0, "NONE"];
[HMT_guetteur, 0.85] call HMT_fnc_kit;
HMT_guetteur disableAI "PATH"; HMT_guetteur setUnitPos "UP";
if (!isNull HMT_TOUR) then {
	private _pts = HMT_TOUR buildingPos -1;
	if (count _pts > 1) then { HMT_guetteur setPosATL (_pts select ((count _pts) - 1)) };
};
HMT_gTour setBehaviour "AWARE"; HMT_gTour setCombatMode "YELLOW";

// -- deux mitrailleuses servies
HMT_gHmg = createGroup east;
{
	_x params ["_hx","_hy","_hd"];
	private _p = [(HMT_CAMP select 0) + _hx, (HMT_CAMP select 1) + _hy, 0];
	private _s = createVehicle ["O_HMG_01_high_F", _p, [], 0, "CAN_COLLIDE"];
	_s setDir _hd; HMT_props pushBack _s;
	private _g = HMT_gHmg createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
	[_g, 0.7] call HMT_fnc_kit; _g moveInGunner _s;
} forEach [[32,10,100],[-12,32,345]];
HMT_gHmg setBehaviour "SAFE"; HMT_gHmg setCombatMode "YELLOW";

// -- garnison de l'avant-poste
HMT_gRelais = createGroup east;
{ private _u = HMT_gRelais createUnit [_x, HMT_RELAIS getPos [8 + random 8, random 360], [], 0, "NONE"]; [_u] call HMT_fnc_kit; }
	forEach ["O_Soldier_TL_F","O_Soldier_F","O_Soldier_F","O_Soldier_AR_F"];
HMT_gRelais setBehaviour "SAFE"; HMT_gRelais setCombatMode "YELLOW"; HMT_gRelais setSpeedMode "LIMITED";
[HMT_gRelais, HMT_RELAIS, 30] call BIS_fnc_taskPatrol;

// -- le blinde qui tourne : il eclaire et il tue
if (["O_MRAP_02_hmg_F"] call HMT_fnc_has) then {
	HMT_gVeh = createGroup east;
	HMT_veh = createVehicle ["O_MRAP_02_hmg_F", HMT_CAMP getPos [260, random 360], [], 0, "NONE"];
	{ private _u = HMT_gVeh createUnit [_x, HMT_CAMP, [], 0, "NONE"]; [_u, 0.7] call HMT_fnc_kit; } forEach ["O_crew_F","O_crew_F"];
	(units HMT_gVeh) select 0 moveInDriver HMT_veh;
	(units HMT_gVeh) select 1 moveInGunner HMT_veh;
	HMT_gVeh setBehaviour "SAFE"; HMT_gVeh setCombatMode "YELLOW"; HMT_gVeh setSpeedMode "LIMITED";
	[HMT_gVeh, HMT_CAMP, 320] call BIS_fnc_taskPatrol;
};

// ---------------------------------------------------------------------
// 4. LA CIBLE — et ses deux ombres
// ---------------------------------------------------------------------
HMT_gHvt = createGroup east;
HMT_HVT = HMT_gHvt createUnit ["O_officer_F", HMT_CAMP getPos [8, 40], [], 0, "NONE"];
[HMT_HVT, 0.55] call HMT_fnc_kit;
HMT_HVT setName "Colonel Vahid Karimi";
{ private _u = HMT_gHvt createUnit ["O_Soldier_TL_F", HMT_CAMP getPos [10, random 360], [], 0, "NONE"]; [_u, 0.75] call HMT_fnc_kit; } forEach [0,1];
HMT_gHvt setBehaviour "SAFE"; HMT_gHvt setCombatMode "YELLOW"; HMT_gHvt setSpeedMode "LIMITED";
HMT_gHvt selectLeader HMT_HVT;

// son vehicule de fuite, portes ouvertes, moteur pret
HMT_fuite_veh = objNull;
if (["O_Truck_02_covered_F"] call HMT_fnc_has) then {
	HMT_fuite_veh = createVehicle ["O_Truck_02_covered_F", HMT_CAMP getPos [40, (HMT_CAMP getDir HMT_OP) + 180], [], 0, "NONE"];
	HMT_fuite_veh setDir (HMT_CAMP getDir HMT_FUITE);
};

// il fait la navette entre le QG et la baraque : jamais deux fois au meme endroit
[] spawn {
	waitUntil { sleep 1; HMT_ready };
	private _a = HMT_CAMP getPos [7, 40];
	private _b = HMT_CAMP getPos [24, 155];
	private _k = 0;
	while { alive HMT_HVT && !HMT_alarme } do {
		HMT_HVT doMove (if (_k % 2 == 0) then { _a } else { _b });
		_k = _k + 1;
		sleep (120 + random 80);
	};
};

diag_log format ["[SN] hommes est = %1", count (allUnits select { side _x == east })];

// ---------------------------------------------------------------------
// 5. L'ALARME — irreversible, et elle fait PARTIR la cible
// ---------------------------------------------------------------------
HMT_fnc_fuite = {
	if (HMT_hvtFui || !alive HMT_HVT) exitWith {};
	HMT_hvtFui = true;
	if (!isNull HMT_fuite_veh && { alive HMT_fuite_veh }) then {
		HMT_HVT assignAsDriver HMT_fuite_veh;
		[HMT_HVT] orderGetIn true;
		{ _x assignAsCargo HMT_fuite_veh; } forEach (units HMT_gHvt - [HMT_HVT]);
		(units HMT_gHvt - [HMT_HVT]) orderGetIn true;
	};
	HMT_gHvt setBehaviour "CARELESS"; HMT_gHvt setSpeedMode "FULL";
	private _w = HMT_gHvt addWaypoint [HMT_FUITE, 0];
	_w setWaypointType "MOVE"; _w setWaypointSpeed "FULL";
	"Il monte en voiture." remoteExec ["hint", 0];
};

[] spawn {
	waitUntil { sleep 1; !isNull player && HMT_ready };
	while { !HMT_alarme && alive player } do {
		sleep 1.5;
		if ((east knowsAbout player) > 1.5) then { HMT_alarme = true };
	};
	if (!HMT_alarme) exitWith {};
	HMT_detecte = true;
	{ _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSpeedMode "FULL"; }
		forEach [HMT_gCamp, HMT_gP1, HMT_gP2, HMT_gTour, HMT_gHmg, HMT_gRelais];
	if (!isNil "HMT_gVeh") then { HMT_gVeh setBehaviour "COMBAT"; HMT_gVeh setCombatMode "RED"; HMT_gVeh setSpeedMode "FULL";
		while { count (waypoints HMT_gVeh) > 0 } do { deleteWaypoint ((waypoints HMT_gVeh) select 0) };
		private _w = HMT_gVeh addWaypoint [getPos player, 0]; _w setWaypointType "SAD"; };
	[] spawn { for "_i" from 1 to 8 do {
		private _p = HMT_CAMP getPos [random 70, random 360];
		createVehicle ["F_40mm_White", [_p select 0, _p select 1, 160], [], 0, "CAN_COLLIDE"]; sleep 20; }; };
	call HMT_fnc_fuite;
	"ALERTE GENERALE. La cible decroche." remoteExec ["hint", 0];
};

// le depart a l'heure, meme sans alarme : le temps est un adversaire
[] spawn {
	waitUntil { sleep 1; HMT_ready };
	sleep HMT_LIMITE;
	if (alive HMT_HVT && !HMT_hvtMort) then {
		"Le convoi demarre." remoteExec ["hint", 0];
		call HMT_fnc_fuite;
	};
};

// ---------------------------------------------------------------------
// 6. SUIVI DE LA CIBLE
// ---------------------------------------------------------------------
HMT_HVT addEventHandler ["Killed", { HMT_hvtMort = true; }];
[] spawn {
	waitUntil { sleep 2; HMT_hvtMort || { HMT_hvtFui && { (HMT_HVT distance2D HMT_CAMP) > 1500 } } };
	if (HMT_hvtMort) then { ["tHvt","SUCCEEDED"] call BIS_fnc_taskSetState }
	else { HMT_echappe = true; ["tHvt","FAILED"] call BIS_fnc_taskSetState };
};

// ---------------------------------------------------------------------
// 7. MARQUEURS ET TACHES
// ---------------------------------------------------------------------
{
	_x params ["_n","_p","_t","_c","_txt","_al"];
	private _m = createMarker [_n, _p];
	_m setMarkerShape "ICON"; _m setMarkerType _t; _m setMarkerColor _c;
	_m setMarkerText _txt; _m setMarkerAlpha _al;
} forEach [
	["m_insert", HMT_INSERT, "mil_start",  "ColorBLUFOR", "Mise a terre", 1],
	["m_op",     HMT_OP,     "mil_objective","ColorBLUFOR","Point d'observation", 1],
	["m_relais", HMT_RELAIS, "o_installation","ColorOPFOR","Avant-poste", 1],
	["m_camp",   HMT_CAMP,   "o_hq",        "ColorOPFOR", "Camp — non localise", 0],
	["m_exfil",  HMT_EXFIL,  "mil_pickup",  "ColorBLUFOR","Exfiltration", 0]
];

[west, "tIntel", ["L'avant-poste tient un terminal. Il dira ou dort la cible.", "Localiser la cible", "m_relais"], HMT_RELAIS, "CREATED", 10, true, "documents"] call BIS_fnc_taskCreate;
[west, "tHvt", ["Neutraliser le colonel Karimi. Il porte l'uniforme d'officier et ne se deplace jamais seul.", "Neutraliser la cible", "m_relais"], HMT_RELAIS, "CREATED", 9, true, "kill"] call BIS_fnc_taskCreate;

if (count HMT_manquantes > 0) then { diag_log format ["[SN] classes absentes : %1", HMT_manquantes] };
HMT_ready = true; publicVariable "HMT_ready"; publicVariable "HMT_OP_GAIN"; publicVariable "HMT_OP_VUE";
diag_log "[SN] monde pret";
