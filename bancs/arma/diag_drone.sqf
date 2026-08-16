// diag_drone.sqf — POURQUOI le drone ne voit rien.
// La sonde principale lit `saitdrone = 0` sur 7 reps consecutives, vehicule ET equipage
// interroges. Avant de deviner, on regarde : 4 montages, 8 lectures chacun, 3 min.
// Ce script ne juge rien. Il REGARDE.

HMT_LOG = { diag_log _this };
HMT_DG_O = [4644, 5652];

HMT_DG_ESSAI = {
    params ["_nom", "_type", "_alt", "_mode", "_cm"];
    private _ox = HMT_DG_O select 0; private _oy = HMT_DG_O select 1;

    // l ennemi : debout, inerte, indestructible — exactement celui de la sonde
    private _ge = createGroup east;
    private _e = _ge createUnit ["O_Soldier_F", [_ox, _oy, 0], [], 0, "NONE"];
    _e setPosATL [_ox, _oy, 0];
    _e disableAI "ALL"; _e setBehaviour "CARELESS"; _e setUnitPos "UP"; _e allowDamage false;
    sleep 1;

    private _d = createVehicle [_type, [_ox, _oy, _alt], [], 0, "FLY"];
    createVehicleCrew _d;
    _d flyInHeight _alt;
    private _g = group (driver _d);
    _g setBehaviour _mode;
    _g setCombatMode _cm;
    _d doMove [_ox, _oy, _alt];

    for "_k" from 1 to 8 do {
        sleep 5;
        private _saitVeh = _d knowsAbout _e;
        private _saitEq = 0;
        { _saitEq = _saitEq max (_x knowsAbout _e) } forEach (crew _d);
        private _saitCamp = west knowsAbout _e;
        private _nt = 0;
        if (count (crew _d) > 0) then { _nt = count ((crew _d select 0) nearTargets 800) };
        private _pd = getPosATL _d;
        (format ["HMT|DG|%1|t|%2|equipage|%3|alt|%4|dist2D|%5|saitVeh|%6|saitEq|%7|saitCamp|%8|nearT|%9",
                 _nom, _k * 5, count (crew _d), round (_pd select 2),
                 round (_d distance2D _e),
                 round (100 * _saitVeh) / 100, round (100 * _saitEq) / 100,
                 round (100 * _saitCamp) / 100, _nt]) call HMT_LOG;
    };

    { deleteVehicle _x } forEach (crew _d);
    deleteVehicle _d; deleteGroup _g;
    deleteVehicle _e; deleteGroup _ge;
    sleep 3;
};

[] spawn {
    sleep 20;
    "HMT|DG|debut" call HMT_LOG;
    // on fait varier UNE chose a la fois : l altitude, puis le combatMode, puis l engin
    ["darter_100_BLUE",   "B_UAV_01_F", 100, "AWARE", "BLUE"]   call HMT_DG_ESSAI;
    ["darter_100_YELLOW", "B_UAV_01_F", 100, "AWARE", "YELLOW"] call HMT_DG_ESSAI;
    ["darter_50_YELLOW",  "B_UAV_01_F",  50, "AWARE", "YELLOW"] call HMT_DG_ESSAI;
    ["greyhawk_150_YELL", "B_UAV_02_F", 150, "AWARE", "YELLOW"] call HMT_DG_ESSAI;
    "HMT|DG|TERMINE" call HMT_LOG;
};
