enableDynamicSimulationSystem true;
"Group" setDynamicSimulationDistance 800;
"Vehicle" setDynamicSimulationDistance 900;
"EmptyVehicle" setDynamicSimulationDistance 300;
"Prop" setDynamicSimulationDistance 60;

if (isNil "HMT_FOB_OBJ") then { HMT_FOB_OBJ = []; };
if (isNil "HMT_FOB_GRP") then { HMT_FOB_GRP = []; };
{ if (!isNull _x) then { { deleteVehicle _x } forEach (crew _x); deleteVehicle _x; } } forEach HMT_FOB_OBJ;
{ if (!isNull _x) then { { deleteVehicle _x } forEach (units _x); deleteGroup _x; } } forEach HMT_FOB_GRP;
HMT_FOB_OBJ = []; HMT_FOB_GRP = []; HMT_FOB_MEN = [];

HMT_LAND = {
    params ["_p"];
    private _res = _p;
    if (surfaceIsWater _p) then {
        private _r = 100;
        while { _r <= 800 && surfaceIsWater _res } do {
            private _k = 0;
            while { _k < 12 && surfaceIsWater _res } do {
                private _a = _k * 30;
                private _c = [(_p select 0) + _r * sin(_a), (_p select 1) + _r * cos(_a), 0];
                if (!surfaceIsWater _c) then { _res = _c; };
                _k = _k + 1;
            };
            _r = _r + 100;
        };
    };
    _res
};

HMT_KIT = {
    params ["_u","_role"];
    _u linkItem "rhs_1PN138";
    _u addItem "ACE_EarPlugs"; _u addItem "ACE_MapTools";
    if ((backpack _u) == "") then { _u addBackpack "rhs_rd54"; };
    if (_role in ["rifleman","at","officer","medic","sergeant"]) then { _u addPrimaryWeaponItem "rhs_acc_1p78"; };
    _u addMagazines ["rhs_mag_rgd5", 2]; _u addMagazines ["rhs_mag_rdg2_white", 2];
    { _u addItem _x } forEach ["ACE_fieldDressing","ACE_fieldDressing","ACE_packingBandage","ACE_packingBandage","ACE_elasticBandage","ACE_tourniquet","ACE_tourniquet","ACE_morphine","ACE_epinephrine","ACE_splint"];
    if (_role == "medic") then { { _u addItem _x } forEach ["ACE_surgicalKit","ACE_personalAidKit","ACE_bloodIV","ACE_bloodIV","ACE_salineIV"]; for "_k" from 1 to 6 do { _u addItem "ACE_fieldDressing"; }; for "_k" from 1 to 3 do { _u addItem "ACE_morphine"; _u addItem "ACE_epinephrine"; }; };
    if (_role == "officer") then { _u linkItem "ACE_microDAGR"; };
};

HMT_FOB_BUILD = {
    params ["_o", "_tier"];
    _o = [_o] call HMT_LAND;
    private _main = (_tier == "MAIN");
    private _nb  = if (_main) then { 12 } else { 8 };
    private _rad = if (_main) then { 36 } else { 26 };
    private _mk = {
        params ["_cls", "_dx", "_dy", "_dir"];
        private _p = [(_o select 0) + _dx, (_o select 1) + _dy, 0];
        private _obj = createVehicle [_cls, _p, [], 0, "CAN_COLLIDE"];
        _obj setDir _dir; _obj setPosATL _p; HMT_FOB_OBJ pushBack _obj; _obj
    };
    ["Land_Cargo_HQ_V1_F", 0, 0, 0] call _mk;
    ["Land_Cargo_House_V1_F", 12, 4, 0] call _mk;
    ["Land_Cargo_Patrol_V1_F", -18, 18, 0] call _mk;
    private _i = 0;
    while { _i < _nb } do { private _a = _i * (360 / _nb); ["Land_HBarrierBig_F", _rad * sin(_a), _rad * cos(_a), _a] call _mk; _i = _i + 1; };
    private _statics = [];
    _statics pushBack (["rhs_KORD_high_MSV", -15, 15, 135] call _mk);
    if (_main) then {
        _statics pushBack (["rhs_KORD_high_MSV", 15, -15, 315] call _mk);
        _statics pushBack (["O_Mortar_01_F", 6, -16, 0] call _mk);
        _statics pushBack (["O_static_AA_F", -6, -22, 0] call _mk);
    };
    private _gs = createGroup east; HMT_FOB_GRP pushBack _gs; _gs enableDynamicSimulation true;
    { private _u = _gs createUnit ["rhs_msv_machinegunner", position _x, [], 0, "NONE"]; _u moveInGunner _x; HMT_FOB_OBJ pushBack _u; HMT_FOB_MEN pushBack [_u, "machinegunner"]; } forEach _statics;
    private _b1 = ["Box_East_Wps_F", 4, 5, 0] call _mk;
    clearWeaponCargoGlobal _b1; clearMagazineCargoGlobal _b1; clearItemCargoGlobal _b1;
    { _b1 addWeaponCargoGlobal [_x, 6]; } forEach ["rhs_weap_ak74m","rhs_weap_ak103","rhs_weap_pkp","rhs_weap_svdp","rhs_weap_rpg7"];
    if (_main && {!isNil { missionNamespace getVariable "ace_arsenal_fnc_initBox" }}) then { private _b2 = ["Box_East_Wps_F", 4, -5, 0] call _mk; [_b2, true] call ace_arsenal_fnc_initBox; };
    private _comp = if (_main) then {
        ["rhs_msv_officer","rhs_msv_sergeant","rhs_msv_rifleman","rhs_msv_rifleman","rhs_msv_machinegunner","rhs_msv_at","rhs_msv_marksman","rhs_msv_medic"]
    } else {
        ["rhs_msv_sergeant","rhs_msv_rifleman","rhs_msv_machinegunner","rhs_msv_at","rhs_msv_marksman","rhs_msv_medic"]
    };
    private _g = 0;
    while { _g < 3 } do {
        private _grp = createGroup east; HMT_FOB_GRP pushBack _grp; _grp enableDynamicSimulation true;
        { private _pos = [(_o select 0) + 6 + _g * 5, (_o select 1) - 12 - _forEachIndex * 2, 0]; private _u = _grp createUnit [_x, _pos, [], 3, "FORM"]; HMT_FOB_OBJ pushBack _u; HMT_FOB_MEN pushBack [_u, _x select [8]]; } forEach _comp;
        _grp setBehaviour "SAFE"; _grp setCombatMode "YELLOW"; _grp allowFleeing 0;
        if (!isNil { missionNamespace getVariable "lambs_wp_fnc_taskGarrison" }) then { [_grp, _o, _rad + 10] call lambs_wp_fnc_taskGarrison; };
        _g = _g + 1;
    };
    ["rhs_tigr_msv", 22, 12, 90] call _mk;
    if (_main) then { ["RHS_Ural_MSV_01", 26, 16, 90] call _mk; ["rhs_btr70_msv", 26, -12, 90] call _mk; };
};

private _net = [
    [[4279,3856,0],"MAIN"],[[2050,5700,0],"MAIN"],[[3253,2984,0],"MAIN"],[[6544,4863,0],"MAIN"],[[4886,5948,0],"MAIN"],[[2915,6165,0],"MAIN"],
    [[1942,3557,0],"OUTPOST"],[[4319,4398,0],"OUTPOST"],[[4604,5284,0],"OUTPOST"],[[3338,5744,0],"OUTPOST"],[[3027,2184,0],"OUTPOST"],[[4206,2715,0],"OUTPOST"],[[1935,2723,0],"OUTPOST"],[[6402,5427,0],"OUTPOST"],[[2979,1860,0],"OUTPOST"],[[2719,1712,0],"OUTPOST"],[[2024,1790,0],"OUTPOST"],[[6157,4349,0],"OUTPOST"],[[5440,3687,0],"OUTPOST"],[[1784,4134,0],"OUTPOST"],[[1790,3512,0],"OUTPOST"],[[2648,5990,0],"OUTPOST"],[[4241,2498,0],"OUTPOST"],[[5691,6124,0],"OUTPOST"],[[1845,2656,0],"OUTPOST"]
];
{ [_x select 0, _x select 1] call HMT_FOB_BUILD; sleep 0.15; } forEach _net;
sleep 1;
{ [_x select 0, _x select 1] call HMT_KIT; if (_forEachIndex mod 50 == 0) then { sleep 0.2; }; } forEach HMT_FOB_MEN;
private _men = (HMT_FOB_MEN apply { _x select 0 }) select { !isNull _x };
diag_log format ["HARMATTAN_FOBNET fobs=%1 objs=%2 grps=%3 men=%4", count _net, count HMT_FOB_OBJ, count HMT_FOB_GRP, count _men];
[] spawn { sleep 20; for "_i" from 1 to 4 do { diag_log format ["HARMATTAN_LOAD t=%1s east=%2 fps=%3", _i*30, count (allUnits select {side _x == east && alive _x}), round diag_fps]; sleep 30; }; };
