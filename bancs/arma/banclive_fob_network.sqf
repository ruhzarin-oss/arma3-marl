// fob_network.sqf — reseau de FOB russes (RHS AFRF) sur Stratis. Idempotent.
if (isNil "HMT_FOB_OBJ") then { HMT_FOB_OBJ = []; };
if (isNil "HMT_FOB_GRP") then { HMT_FOB_GRP = []; };
{ if (!isNull _x) then { { deleteVehicle _x } forEach (crew _x); deleteVehicle _x; } } forEach HMT_FOB_OBJ;
{ if (!isNull _x) then { { deleteVehicle _x } forEach (units _x); deleteGroup _x; } } forEach HMT_FOB_GRP;
HMT_FOB_OBJ = []; HMT_FOB_GRP = [];

HMT_FOB_BUILD = {
    params ["_o", "_tier"];
    private _main = (_tier == "MAIN");
    private _nb  = if (_main) then { 12 } else { 8 };
    private _rad = if (_main) then { 36 } else { 26 };

    private _mk = {
        params ["_cls", "_dx", "_dy", "_dir"];
        private _p = [(_o select 0) + _dx, (_o select 1) + _dy, 0];
        private _obj = createVehicle [_cls, _p, [], 0, "CAN_COLLIDE"];
        _obj setDir _dir;
        _obj setPosATL _p;
        HMT_FOB_OBJ pushBack _obj;
        _obj
    };

    ["Land_Cargo_HQ_V1_F", 0, 0, 0] call _mk;
    ["Land_Cargo_House_V1_F", 12, 4, 0] call _mk;
    ["Land_Cargo_Patrol_V1_F", -18, 18, 0] call _mk;

    private _i = 0;
    while { _i < _nb } do {
        private _a = _i * (360 / _nb);
        ["Land_HBarrierBig_F", _rad * sin(_a), _rad * cos(_a), _a] call _mk;
        _i = _i + 1;
    };

    private _statics = [];
    _statics pushBack (["rhs_KORD_high_MSV", -15, 15, 135] call _mk);
    if (_main) then {
        _statics pushBack (["rhs_KORD_high_MSV", 15, -15, 315] call _mk);
        _statics pushBack (["O_Mortar_01_F", 6, -16, 0] call _mk);
        _statics pushBack (["O_static_AA_F", -6, -22, 0] call _mk);
    };
    private _gs = createGroup east;
    HMT_FOB_GRP pushBack _gs;
    {
        private _u = _gs createUnit ["rhs_msv_machinegunner", position _x, [], 0, "NONE"];
        _u moveInGunner _x;
        HMT_FOB_OBJ pushBack _u;
    } forEach _statics;

    private _b1 = ["Box_East_Wps_F", 4, 5, 0] call _mk;
    clearWeaponCargoGlobal _b1;
    clearMagazineCargoGlobal _b1;
    clearItemCargoGlobal _b1;
    {
        _b1 addWeaponCargoGlobal [_x, 6];
    } forEach ["rhs_weap_ak74m", "rhs_weap_ak103", "rhs_weap_aks74u", "rhs_weap_pkp", "rhs_weap_svdp", "rhs_weap_rpg7", "rhs_weap_igla"];
    if (_main && {!isNil { missionNamespace getVariable "ace_arsenal_fnc_initBox" }}) then {
        private _b2 = ["Box_East_Wps_F", 4, -5, 0] call _mk;
        [_b2, true] call ace_arsenal_fnc_initBox;
    };

    private _comp = if (_main) then {
        ["rhs_msv_officer", "rhs_msv_sergeant", "rhs_msv_rifleman", "rhs_msv_rifleman", "rhs_msv_machinegunner", "rhs_msv_at", "rhs_msv_marksman", "rhs_msv_medic"]
    } else {
        ["rhs_msv_sergeant", "rhs_msv_rifleman", "rhs_msv_machinegunner", "rhs_msv_at", "rhs_msv_marksman", "rhs_msv_medic"]
    };
    private _nsq = if (_main) then { 2 } else { 1 };
    private _g = 0;
    while { _g < _nsq } do {
        private _grp = createGroup east;
        HMT_FOB_GRP pushBack _grp;
        {
            private _pos = [(_o select 0) + 6 + _g * 5, (_o select 1) - 12 - _forEachIndex * 2, 0];
            private _u = _grp createUnit [_x, _pos, [], 3, "FORM"];
            HMT_FOB_OBJ pushBack _u;
        } forEach _comp;
        _grp setBehaviour "SAFE";
        _grp setCombatMode "YELLOW";
        _grp allowFleeing 0;
        if (!isNil { missionNamespace getVariable "lambs_wp_fnc_taskGarrison" }) then {
            [_grp, _o, _rad + 10] call lambs_wp_fnc_taskGarrison;
        };
        _g = _g + 1;
    };

    ["rhs_tigr_msv", 22, 12, 90] call _mk;
    if (_main) then {
        ["RHS_Ural_MSV_01", 26, 16, 90] call _mk;
        ["rhs_btr70_msv", 26, -12, 90] call _mk;
        ["RHS_Mi8AMT_vdv", 55, -30, 0] call _mk;
    };
};

private _net = [
    [[2050, 5700, 0], "MAIN"],
    [[3253, 2984, 0], "OUTPOST"],
    [[4886, 5948, 0], "OUTPOST"],
    [[4279, 3856, 0], "OUTPOST"],
    [[1942, 3557, 0], "OUTPOST"]
];
{
    [_x select 0, _x select 1] call HMT_FOB_BUILD;
} forEach _net;

diag_log format ["HARMATTAN_FOBNET fobs=%1 objs=%2 grps=%3", count _net, count HMT_FOB_OBJ, count HMT_FOB_GRP];
