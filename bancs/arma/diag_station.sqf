// diag_station.sqf — QUEL OBSERVATEUR AERIEN TIENT SA STATION *ET* VOIT ?
// Acquis du 16/08 : l ennemi est detectable (observateur d infanterie a 2,87 en 10 s a
// 300 m), le Darter rend 0 sur 4 montages, le Greyhawk a un nearTargets NON NUL mais
// s eloigne a 1850 m en 40 s parce que c est un avion.
// On cherche donc un engin qui SAIT voir et qui RESTE. Trois montages, 40 s chacun.
// Le temoin d infanterie tourne en parallele dans les trois : si LUI voit et pas l engin,
// c est l engin. Il est l etalon, pas un bras.

HMT_LOG = { diag_log _this };
HMT_DS_O = [4644, 5652];

HMT_DS_ESSAI = {
    params ["_nom", "_type", "_alt", "_tenue"];
    private _ox = HMT_DS_O select 0; private _oy = HMT_DS_O select 1;

    private _ge = createGroup east;
    private _e = _ge createUnit ["O_Soldier_F", [_ox, _oy, 0], [], 0, "NONE"];
    _e setPosATL [_ox, _oy, 0];
    _e disableAI "ALL"; _e setBehaviour "CARELESS"; _e setUnitPos "UP"; _e allowDamage false;

    // ETALON : l infanterie qui sait voir, a 300 m, face a lui
    private _go = createGroup west;
    private _o = _go createUnit ["B_Soldier_F", [_ox, _oy - 300, 0], [], 0, "NONE"];
    _o setPosATL [_ox, _oy - 300, 0]; _o setSkill 0.5; _o setDir 0;
    _o disableAI "PATH"; _o setBehaviour "COMBAT"; _o setCombatMode "RED"; _o allowDamage false;

    private _d = createVehicle [_type, [_ox, _oy, _alt], [], 0, "FLY"];
    createVehicleCrew _d;
    _d flyInHeight _alt;
    private _gd = group (driver _d);
    _gd setBehaviour "AWARE"; _gd setCombatMode "YELLOW";
    if (_tenue == "attache") then {
        // on le CLOUE au-dessus de l ennemi : plus de vol, donc plus de derive
        _d attachTo [_e, [0, 0, _alt]];
    } else {
        _d doMove [_ox, _oy, _alt];
    };

    for "_k" from 1 to 8 do {
        // "domove" : on REPETE l ordre, l engin revient sans cesse au-dessus de la cible
        if (_tenue == "domove") then { _d doMove [_ox, _oy, _alt] };
        sleep 5;
        private _sd = _d knowsAbout _e;
        { _sd = _sd max (_x knowsAbout _e) } forEach (crew _d);
        private _nt = 0;
        if (count (crew _d) > 0) then { _nt = count ((crew _d select 0) nearTargets 800) };
        (format ["HMT|DS|%1|t|%2|drone|%3|etalon|%4|camp|%5|dist2D|%6|alt|%7|nearT|%8",
                 _nom, _k * 5,
                 round (100 * _sd) / 100,
                 round (100 * (_o knowsAbout _e)) / 100,
                 round (100 * (west knowsAbout _e)) / 100,
                 round (_d distance2D _e), round ((getPosATL _d) select 2), _nt]) call HMT_LOG;
    };

    if (_tenue == "attache") then { detach _d };
    { deleteVehicle _x } forEach (crew _d);
    deleteVehicle _d; deleteGroup _gd;
    deleteVehicle _o; deleteGroup _go;
    deleteVehicle _e; deleteGroup _ge;
    sleep 3;
};

[] spawn {
    sleep 20;
    "HMT|DS|debut" call HMT_LOG;
    ["greyhawk_domove",  "B_UAV_02_F",       150, "domove"]  call HMT_DS_ESSAI;
    ["greyhawk_attache", "B_UAV_02_F",       150, "attache"] call HMT_DS_ESSAI;
    ["helico_domove",    "B_Heli_Light_01_F", 80, "domove"]  call HMT_DS_ESSAI;
    "HMT|DS|TERMINE" call HMT_LOG;
};
