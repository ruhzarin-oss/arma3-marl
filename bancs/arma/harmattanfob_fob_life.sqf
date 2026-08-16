HMT_FOB_ANCHORS = [
    [4279,3856,0],[2050,5700,0],[3253,2984,0],[6544,4863,0],[4886,5948,0],[2915,6165,0],
    [1942,3557,0],[4319,4398,0],[4604,5284,0],[3338,5744,0],[3027,2184,0],[4206,2715,0],
    [1935,2723,0],[6402,5427,0],[2979,1860,0],[2719,1712,0],[2024,1790,0],[6157,4349,0],
    [5440,3687,0],[1784,4134,0],[1790,3512,0],[2648,5990,0],[4241,2498,0],[5691,6124,0],[1845,2656,0]
];
if (isNil "HMT_LIFE_OBJ") then { HMT_LIFE_OBJ = []; };
{ if (!isNull _x) then { { deleteVehicle _x } forEach (crew _x); deleteVehicle _x; } } forEach HMT_LIFE_OBJ;
HMT_LIFE_OBJ = []; HMT_QRF_COOLDOWN = 0;

private _pp = 0;
while { _pp < 5 } do {
    private _start = [HMT_FOB_ANCHORS select _pp] call HMT_LAND;
    private _grp = createGroup east;
    private _veh = createVehicle ["rhs_tigr_msv", _start, [], 18, "NONE"];
    HMT_LIFE_OBJ pushBack _veh;
    private _drv = _grp createUnit ["rhs_msv_rifleman", _start, [], 5, "FORM"]; _drv moveInDriver _veh; HMT_LIFE_OBJ pushBack _drv;
    private _gnr = _grp createUnit ["rhs_msv_machinegunner", _start, [], 5, "FORM"]; _gnr moveInGunner _veh; HMT_LIFE_OBJ pushBack _gnr;
    private _cc = 0;
    while { _cc < 2 } do { private _u = _grp createUnit ["rhs_msv_rifleman", _start, [], 5, "FORM"]; _u moveInCargo _veh; HMT_LIFE_OBJ pushBack _u; _cc = _cc + 1; };
    private _ai = 0;
    while { _ai < (count HMT_FOB_ANCHORS) } do {
        private _wp = _grp addWaypoint [(HMT_FOB_ANCHORS select _ai), 30];
        _wp setWaypointType "MOVE"; _wp setWaypointSpeed "LIMITED"; _wp setWaypointBehaviour "SAFE";
        _ai = _ai + 5;
    };
    private _cyc = _grp addWaypoint [_start, 30]; _cyc setWaypointType "CYCLE";
    _grp setBehaviour "SAFE"; _grp setSpeedMode "LIMITED"; _grp setCombatMode "YELLOW";
    _pp = _pp + 1;
};

[] spawn {
    while { true } do {
        sleep 8;
        if (time >= HMT_QRF_COOLDOWN) then {
            private _threats = allUnits select { (side _x != east) && (side _x != civilian) && alive _x && (east knowsAbout _x > 1) };
            if (count _threats > 0) then {
                private _hit = objNull; private _fob = [];
                {
                    private _t = _x; private _f = [];
                    { if ((_t distance _x) < 400) exitWith { _f = _x; }; } forEach HMT_FOB_ANCHORS;
                    if (count _f > 0) exitWith { _hit = _t; _fob = _f; };
                } forEach _threats;
                if (!isNull _hit) then {
                    private _near = HMT_FOB_ANCHORS select 0; private _bd = 1e9;
                    { private _d = _x distance _hit; if (_d < _bd) then { _bd = _d; _near = _x; }; } forEach HMT_FOB_ANCHORS;
                    private _qrf = createGroup east; private _qi = 0;
                    while { _qi < 6 } do { private _u = _qrf createUnit ["rhs_msv_rifleman", _near, [], 10, "FORM"]; HMT_LIFE_OBJ pushBack _u; _qi = _qi + 1; };
                    _qrf setBehaviour "AWARE"; _qrf setCombatMode "RED"; _qrf setSpeedMode "FULL";
                    _qrf move (getPosATL _hit); { _x doMove (getPosATL _hit) } forEach units _qrf;
                    diag_log format ["HARMATTAN_QRF dispatch fob=%1 menace=%2 dist=%3", _fob, typeOf _hit, round _bd];
                    HMT_QRF_COOLDOWN = time + 150;
                };
            };
        };
    };
};
diag_log format ["HARMATTAN_LIFE patrouilles=5 anchors=%1 qrf=ON", count HMT_FOB_ANCHORS];
