// diag_cible.sqf — MON ENNEMI EST-IL SEULEMENT DETECTABLE ?
// Le drone rend knowsAbout=0 sur 4 montages. Deux lectures possibles, et elles n ont
// pas du tout les memes consequences :
//   (a) le DRONE ne sait pas voir            -> seul le bras A1 tombe
//   (b) l ENNEMI n est pas detectable        -> le zero du bras A0 n est PAS l angle mort,
//       c est un homme que personne ne peut voir, et la porte P2 ne vaut RIEN.
// On tranche avec un OBSERVATEUR D INFANTERIE, qui lui sait voir, place FACE a l ennemi
// a 300 m. Trois etats d ennemi, du plus bride au plus natif.

HMT_LOG = { diag_log _this };
HMT_DC_O = [4644, 5652];

HMT_DC_ESSAI = {
    params ["_nom", "_bride"];
    private _ox = HMT_DC_O select 0; private _oy = HMT_DC_O select 1;

    private _ge = createGroup east;
    private _e = _ge createUnit ["O_Soldier_F", [_ox, _oy, 0], [], 0, "NONE"];
    _e setPosATL [_ox, _oy, 0];
    _e setUnitPos "UP"; _e allowDamage false;
    switch (_bride) do {
        case "ALL":    { _e disableAI "ALL"; _e setBehaviour "CARELESS" };
        case "STATUE": { _e disableAI "PATH"; _e disableAI "FSM"; _e disableAI "AUTOCOMBAT";
                         _e setBehaviour "CARELESS" };
        case "NATIF":  { _e setBehaviour "CARELESS" };
    };

    // L OBSERVATEUR : infanterie west, 300 m, FACE a l ennemi (donc DANS son cone),
    // immobile, IA entiere. Si LUI ne voit pas, personne ne peut voir.
    private _go = createGroup west;
    private _ox2 = _ox; private _oy2 = _oy - 300;
    private _o = _go createUnit ["B_Soldier_F", [_ox2, _oy2, 0], [], 0, "NONE"];
    _o setPosATL [_ox2, _oy2, 0]; _o setSkill 0.5;
    _o setDir 0;                              // il regarde vers +y, donc vers l ennemi
    _o disableAI "PATH";                      // il reste sur place, il garde ses yeux
    _o setBehaviour "COMBAT"; _o setCombatMode "RED"; _o allowFleeing 0;
    _o allowDamage false;

    // le drone, en comparaison, au meme instant
    private _d = createVehicle ["B_UAV_01_F", [_ox, _oy, 100], [], 0, "FLY"];
    createVehicleCrew _d;
    _d flyInHeight 100;
    private _gd = group (driver _d);
    _gd setBehaviour "AWARE"; _gd setCombatMode "YELLOW";
    _d doMove [_ox, _oy, 100];

    private _vue = 0;
    for "_k" from 1 to 8 do {
        sleep 5;
        _vue = [objNull, "VIEW"] checkVisibility [eyePos _o, eyePos _e];
        private _sd = _d knowsAbout _e;
        { _sd = _sd max (_x knowsAbout _e) } forEach (crew _d);
        (format ["HMT|DC|%1|t|%2|obs|%3|drone|%4|camp|%5|vue|%6|dist|%7",
                 _nom, _k * 5,
                 round (100 * (_o knowsAbout _e)) / 100,
                 round (100 * _sd) / 100,
                 round (100 * (west knowsAbout _e)) / 100,
                 round (100 * _vue) / 100,
                 round (_o distance2D _e)]) call HMT_LOG;
    };

    { deleteVehicle _x } forEach (crew _d);
    deleteVehicle _d; deleteGroup _gd;
    deleteVehicle _o; deleteGroup _go;
    deleteVehicle _e; deleteGroup _ge;
    sleep 3;
};

[] spawn {
    sleep 20;
    "HMT|DC|debut" call HMT_LOG;
    ["ennemi_disableAI_ALL", "ALL"]    call HMT_DC_ESSAI;   // celui de la sonde
    ["ennemi_STATUE",        "STATUE"] call HMT_DC_ESSAI;
    ["ennemi_NATIF",         "NATIF"]  call HMT_DC_ESSAI;   // verite terrain : ca DOIT etre vu
    "HMT|DC|TERMINE" call HMT_LOG;
};
