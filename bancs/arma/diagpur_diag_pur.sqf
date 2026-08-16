// diag_pur.sqf — UN OEIL AERIEN VOIT-IL QUOI QUE CE SOIT, SEUL ?
// ⚠️ CE SCRIPT CORRIGE UNE FAUTE DE MESURE. Le diagnostic precedent concluait que
// l helicoptere percevait (2,87 a 25 s). FAUX : il y avait un ETALON D INFANTERIE dans
// la meme scene, qui savait a 2,87 des 10 s, et la connaissance est DE CAMP. L engin
// n a pas vu, il a HERITE — le decalage de 15 s le trahissait, je ne l ai pas lu.
// L etalon contaminait la mesure qu il devait valider.
//
// Ici, SCENE PURE : l ennemi et UN SEUL observateur. Rien d autre du camp west.
// E3 est le controle positif du diagnostic lui-meme : si l infanterie SEULE ne voit
// pas non plus, la scene est en cause et rien ne se lit.

HMT_LOG = { diag_log _this };
HMT_DP_O = [4644, 5652];

HMT_DP_ESSAI = {
    params ["_nom", "_genre", "_type", "_alt", "_ecart"];
    private _ox = HMT_DP_O select 0; private _oy = HMT_DP_O select 1;

    private _ge = createGroup east;
    private _e = _ge createUnit ["O_Soldier_F", [_ox, _oy, 0], [], 0, "NONE"];
    _e setPosATL [_ox, _oy, 0];
    _e disableAI "ALL"; _e setBehaviour "CARELESS"; _e setUnitPos "UP"; _e allowDamage false;
    sleep 1;

    private _obs = objNull; private _g = grpNull;
    if (_genre == "air") then {
        private _d = createVehicle [_type, [_ox, _oy - _ecart, _alt], [], 0, "FLY"];
        createVehicleCrew _d;
        _d flyInHeight _alt;
        _g = group (driver _d);
        _g setBehaviour "AWARE"; _g setCombatMode "YELLOW";
        _obs = _d;
    } else {
        _g = createGroup west;
        private _u = _g createUnit ["B_Soldier_F", [_ox, _oy - _ecart, 0], [], 0, "NONE"];
        _u setPosATL [_ox, _oy - _ecart, 0]; _u setSkill 0.5; _u setDir 0;
        _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowDamage false;
        _obs = _u;
    };

    for "_k" from 1 to 12 do {
        if (_genre == "air") then { _obs doMove [_ox, _oy, _alt] };
        sleep 5;
        private _s = _obs knowsAbout _e;
        if (_genre == "air") then { { _s = _s max (_x knowsAbout _e) } forEach (crew _obs) };
        (format ["HMT|DP|%1|t|%2|obs|%3|camp|%4|dist2D|%5|alt|%6",
                 _nom, _k * 5,
                 round (100 * _s) / 100,
                 round (100 * (west knowsAbout _e)) / 100,
                 round (_obs distance2D _e), round ((getPosATL _obs) select 2)]) call HMT_LOG;
    };

    if (_genre == "air") then { { deleteVehicle _x } forEach (crew _obs) };
    deleteVehicle _obs; deleteGroup _g;
    deleteVehicle _e; deleteGroup _ge;
    sleep 3;
};

[] spawn {
    sleep 20;
    "HMT|DP|debut" call HMT_LOG;
    ["helico_seul_dessus", "air", "B_Heli_Light_01_F", 80, 0]   call HMT_DP_ESSAI;
    ["helico_seul_300m",   "air", "B_Heli_Light_01_F", 80, 300] call HMT_DP_ESSAI;
    ["infanterie_seule",   "sol", "",                   0, 300] call HMT_DP_ESSAI;
    "HMT|DP|TERMINE" call HMT_LOG;
};
