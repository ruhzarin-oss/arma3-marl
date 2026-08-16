// vague 1 : pays vivant sous tension
HMT_WORLD_OBJ = []; HMT_WORLD_GRP = [];

// 1. RYTHME : jour/nuit accelere + meteo dynamique
setTimeMultiplier 4;
86400 setOvercast 0.4; 0 setFog 0.04; forceWeatherChange;
[] spawn { while { true } do { sleep 900; (1800 setOvercast (random 0.85)); forceWeatherChange; sleep 0.1; (1800 setFog (random 0.15)); }; };

// 2. POSTURE vigilante (garnisons)
{ if (!isNull _x) then { _x setBehaviour "AWARE"; _x setCombatMode "YELLOW"; }; } forEach HMT_FOB_GRP;

// 3. VILLES civiles
HMT_TOWNS = [[2915,6165,0],[6544,4863,0],[3027,2184,0],[1935,2723,0],[2719,1712,0]];
private _civT = ["C_man_1","C_man_polo_1_F","C_man_polo_2_F","C_Man_casual_1_F","C_Man_casual_4_F","C_man_w_worker_F","C_man_hunter_1_F"];
{
    private _town = [_x] call HMT_LAND;
    private _grp = createGroup civilian; HMT_WORLD_GRP pushBack _grp; _grp enableDynamicSimulation true;
    for "_c" from 1 to 12 do {
        private _pos = [(_town select 0) + (random 140 - 70), (_town select 1) + (random 140 - 70), 0];
        private _u = _grp createUnit [selectRandom _civT, [_pos] call HMT_LAND, [], 5, "NONE"];
        HMT_WORLD_OBJ pushBack _u;
    };
    if (!isNil { missionNamespace getVariable "lambs_wp_fnc_taskPatrol" }) then { [_grp, _town, 150] call lambs_wp_fnc_taskPatrol; };
    _grp setBehaviour "CARELESS"; _grp setSpeedMode "LIMITED";
} forEach HMT_TOWNS;

// 4. TRAFIC civil (voitures entre villes)
private _vT = ["C_Offroad_01_F","C_Hatchback_01_F","C_SUV_01_F","C_Van_01_transport_F","C_Quadbike_01_F"];
private _tt = 0;
while { _tt < 8 } do {
    private _start = [selectRandom HMT_TOWNS] call HMT_LAND;
    private _grp = createGroup civilian; HMT_WORLD_GRP pushBack _grp; _grp enableDynamicSimulation true;
    private _veh = createVehicle [selectRandom _vT, _start, [], 30, "NONE"]; HMT_WORLD_OBJ pushBack _veh;
    private _drv = _grp createUnit ["C_man_1", _start, [], 5, "FORM"]; _drv moveInDriver _veh; HMT_WORLD_OBJ pushBack _drv;
    { private _wp = _grp addWaypoint [([_x] call HMT_LAND), 20]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "LIMITED"; _wp setWaypointBehaviour "CARELESS"; } forEach HMT_TOWNS;
    private _cyc = _grp addWaypoint [_start, 20]; _cyc setWaypointType "CYCLE";
    _grp setBehaviour "CARELESS"; _grp setSpeedMode "LIMITED";
    _tt = _tt + 1;
};

// 5. PORTS : bateaux de peche (sur leau, pas de HMT_LAND)
private _bays = [[2648,5990,0],[6800,5000,0],[1700,4200,0]];
{
    private _grp = createGroup civilian; HMT_WORLD_GRP pushBack _grp; _grp enableDynamicSimulation true;
    private _boat = createVehicle ["C_Boat_Civil_01_F", _x, [], 20, "NONE"]; HMT_WORLD_OBJ pushBack _boat;
    private _f = _grp createUnit ["C_Man_Fisherman_01_F", _x, [], 5, "FORM"]; _f moveInDriver _boat; HMT_WORLD_OBJ pushBack _f;
    private _wp = _grp addWaypoint [_x, 100]; _wp setWaypointType "MOVE"; private _cyc = _grp addWaypoint [_x, 100]; _cyc setWaypointType "CYCLE";
    _grp setBehaviour "CARELESS"; _grp setSpeedMode "LIMITED";
} forEach _bays;

// 6. BETAIL dans la campagne
private _aT = ["Goat_random_F","Sheep_random_F","Hen_random_F"];
private _an = 0;
while { _an < 24 } do {
    private _t = [selectRandom HMT_TOWNS] call HMT_LAND;
    private _p = [(_t select 0) + (random 360 - 180), (_t select 1) + (random 360 - 180), 0];
    private _ag = createAgent [selectRandom _aT, [_p] call HMT_LAND, [], 0, "NONE"];
    HMT_WORLD_OBJ pushBack _ag;
    _an = _an + 1;
};

// 7. CHECKPOINTS de larmee (controle des acces)
HMT_CHECKPOINTS = [[3100,4050,0],[4450,5050,0],[2600,5450,0],[5200,4700,0]];
{
    private _cp = [_x] call HMT_LAND;
    private _b1 = createVehicle ["Land_BagFence_Long_F", _cp, [], 0, "CAN_COLLIDE"]; HMT_WORLD_OBJ pushBack _b1;
    private _rc = createVehicle ["RoadCone_L_F", [(_cp select 0)+5,(_cp select 1),0], [], 0, "CAN_COLLIDE"]; HMT_WORLD_OBJ pushBack _rc;
    private _tw = createVehicle ["Land_Cargo_Patrol_V1_F", [(_cp select 0)-6,(_cp select 1)+6,0], [], 0, "CAN_COLLIDE"]; HMT_WORLD_OBJ pushBack _tw;
    private _grp = createGroup east; HMT_WORLD_GRP pushBack _grp; _grp enableDynamicSimulation true;
    private _s = 0;
    while { _s < 3 } do { private _u = _grp createUnit ["rhs_msv_rifleman", _cp, [], 4, "NONE"]; [_u,"rifleman"] call HMT_KIT; HMT_WORLD_OBJ pushBack _u; _s = _s + 1; };
    _grp setBehaviour "AWARE"; _grp setCombatMode "YELLOW";
} forEach HMT_CHECKPOINTS;

diag_log format ["HARMATTAN_WORLD villes=%1 checkpoints=%2 objs=%3 grps=%4 timeMult=%5", count HMT_TOWNS, count HMT_CHECKPOINTS, count HMT_WORLD_OBJ, count HMT_WORLD_GRP, timeMultiplier];
