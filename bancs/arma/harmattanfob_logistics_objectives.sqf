// vague 2 : logistique finie + cibles designees
HMT_LOG_OBJ = []; HMT_LOG_GRP = []; HMT_TARGETS = [];

// DEPOTS (2 aux bastions) + carburant + reparation
HMT_DEPOTS = [[4279,3856,0],[2050,5700,0]];
HMT_DEPOT_STOCK = [800,800];
{
    private _d = [_x] call HMT_LAND;
    private _hq = createVehicle ["Land_Cargo_HQ_V1_F", [(_d select 0)+32,(_d select 1)+32,0], [], 0, "CAN_COLLIDE"]; HMT_LOG_OBJ pushBack _hq;
    private _fuel = createVehicle ["C_Van_01_fuel_F", [(_d select 0)+36,(_d select 1)+28,0], [], 0, "NONE"]; HMT_LOG_OBJ pushBack _fuel;
    private _rep = createVehicle ["RHS_Ural_MSV_01", [(_d select 0)+40,(_d select 1)+28,0], [], 0, "NONE"]; HMT_LOG_OBJ pushBack _rep;
    _hq setVariable ["HMT_TARGET","DEPOT"]; HMT_TARGETS pushBack ["DEPOT", _hq];
} forEach HMT_DEPOTS;

// CONVOIS (3 Ural depot -> bases)
private _ci = 0;
while { _ci < 3 } do {
    private _start = [HMT_DEPOTS select (_ci mod 2)] call HMT_LAND;
    private _grp = createGroup east; HMT_LOG_GRP pushBack _grp;
    private _ural = createVehicle ["RHS_Ural_MSV_01", _start, [], 28, "NONE"]; HMT_LOG_OBJ pushBack _ural;
    private _drv = _grp createUnit ["rhs_msv_rifleman", _start, [], 5, "FORM"]; _drv moveInDriver _ural; HMT_LOG_OBJ pushBack _drv;
    { private _wp = _grp addWaypoint [([_x] call HMT_LAND), 25]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "LIMITED"; _wp setWaypointBehaviour "SAFE"; } forEach (HMT_FOB_ANCHORS select [_ci*7, 7]);
    private _back = _grp addWaypoint [_start, 25]; _back setWaypointType "CYCLE";
    _grp setBehaviour "SAFE"; _grp setSpeedMode "LIMITED"; _grp setCombatMode "YELLOW";
    _ci = _ci + 1;
};

// CASERNE : renforts a rythme, stoppe si elle tombe
HMT_CASERNE = createVehicle ["Land_Cargo_HQ_V1_F", [[2915,6165,0]] call HMT_LAND, [], 0, "CAN_COLLIDE"];
HMT_CASERNE setVariable ["HMT_TARGET","CASERNE"]; HMT_TARGETS pushBack ["CASERNE", HMT_CASERNE];
[] spawn {
    sleep 90;
    while { alive HMT_CASERNE } do {
        private _weak = HMT_FOB_ANCHORS select 0; private _min = 1e9;
        { private _a = _x; private _n = {alive _x && {side _x == east} && (_x distance _a) < 90} count allUnits; if (_n < _min) then { _min = _n; _weak = _a; }; } forEach HMT_FOB_ANCHORS;
        // GEL DU BANC : pendant un episode de mesure, la caserne ne fait naitre personne.
        // Sinon 6 hommes tombent du ciel sur le FOB LE PLUS FAIBLE = celui qu'on est en train
        // d'attaquer, et l'effet de l'ordre est noye. Drapeau absent = comportement d'origine.
        private _gel = (!isNil "HMT_PB_GEL") && { HMT_PB_GEL };
        private _g = createGroup east; HMT_LOG_GRP pushBack _g;
        private _k = if (_gel) then { 6 } else { 0 };
        while { _k < 6 } do { private _u = _g createUnit ["rhs_msv_rifleman", getPos HMT_CASERNE, [], 8, "FORM"]; [_u,"rifleman"] call HMT_KIT; _k = _k + 1; };
        _g enableDynamicSimulation true;
        if (!isNil { missionNamespace getVariable "lambs_wp_fnc_taskGarrison" }) then { [_g, _weak, 40] call lambs_wp_fnc_taskGarrison; } else { _g move _weak; };
        if (!_gel) then { diag_log format ["HARMATTAN_LOG renfort 6h -> %1 (faible=%2)", _weak, _min]; };
        sleep 480;
    };
    diag_log "HARMATTAN_LOG CASERNE TOMBEE -> renforts stoppes";
};

// MUNITIONS finies (etat representatif depot -> bases)
HMT_BASE_MUNS = []; { HMT_BASE_MUNS pushBack 100; } forEach HMT_FOB_ANCHORS;
[] spawn {
    while { true } do {
        sleep 180;
        { HMT_BASE_MUNS set [_forEachIndex, ((HMT_BASE_MUNS select _forEachIndex) - 8) max 0]; } forEach HMT_FOB_ANCHORS;
        private _tot = (HMT_DEPOT_STOCK select 0) + (HMT_DEPOT_STOCK select 1);
        if (_tot > 0) then {
            { if ((HMT_BASE_MUNS select _forEachIndex) < 60) then { private _give = 30 min (HMT_DEPOT_STOCK select 0); HMT_BASE_MUNS set [_forEachIndex, (HMT_BASE_MUNS select _forEachIndex) + _give]; HMT_DEPOT_STOCK set [0, ((HMT_DEPOT_STOCK select 0) - _give) max 0]; }; } forEach HMT_FOB_ANCHORS;
        };
        diag_log format ["HARMATTAN_LOG muns depot=%1 rupture=%2", HMT_DEPOT_STOCK, {_x < 30} count HMT_BASE_MUNS];
    };
};

// CIBLES designees
private _qg = createVehicle ["Land_Cargo_HQ_V1_F", [[2922,6172,0]] call HMT_LAND, [], 0, "CAN_COLLIDE"]; _qg setVariable ["HMT_TARGET","QG"]; HMT_TARGETS pushBack ["QG", _qg];
private _hvtG = createGroup east; private _hvt = _hvtG createUnit ["rhs_msv_officer", [[2918,6168,0]] call HMT_LAND, [], 5, "NONE"]; [_hvt,"officer"] call HMT_KIT; _hvt setVariable ["HMT_TARGET","HVT"]; HMT_TARGETS pushBack ["HVT", _hvt]; HMT_LOG_GRP pushBack _hvtG;
private _hosG = createGroup civilian; private _hos = _hosG createUnit ["C_man_p_fugitive_F", [[4279,3850,0]] call HMT_LAND, [], 3, "NONE"]; _hos setVariable ["HMT_TARGET","OTAGE"]; HMT_TARGETS pushBack ["OTAGE", _hos]; HMT_LOG_GRP pushBack _hosG;
{ private _intel = createVehicle ["Box_East_Wps_F", [_x] call HMT_LAND, [], 0, "CAN_COLLIDE"]; _intel setVariable ["HMT_TARGET","INTEL"]; HMT_TARGETS pushBack ["INTEL", _intel]; } forEach [[3253,2980,0],[6544,4860,0]];

diag_log format ["HARMATTAN_LOGI depots=%1 convois=3 cibles=%2 types=%3", count HMT_DEPOTS, count HMT_TARGETS, HMT_TARGETS apply { _x select 0 }];
