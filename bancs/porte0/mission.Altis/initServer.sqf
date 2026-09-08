// =====================================================================
// PORTE ZERO - le monde recompense-t-il le JUGEMENT ?
//
// Deux intentions scriptees, deux rapports de force. Si le classement des
// intentions ne s inverse pas entre les deux rapports, il n y a rien a
// apprendre : le but « choisir selon la situation » n est pas mesurable.
//
// Aucun joueur, aucun pont : le RPT est le journal, lire.py CERTIFIE.
// =====================================================================
P0_VERSION = 1;
P0_LOG = { diag_log _this };
P0_GRAINE = ["P0_GRAINE", 1] call BIS_fnc_getParamValue;
P0_INTENTION = ["P0_INTENTION", 0] call BIS_fnc_getParamValue;   // 0 = ASSAILLIR, 1 = ROMPRE
P0_RATIO = ["P0_RATIO", 0] call BIS_fnc_getParamValue;           // 0 = 3:1, 1 = 1:3
P0_DUREE = ["P0_DUREE", 600] call BIS_fnc_getParamValue;
P0_REPS = ["P0_REPS", 4] call BIS_fnc_getParamValue;             // repetitions dans la graine

P0_RNG = ((P0_GRAINE * 7919) + 104729) % 65537;
if (P0_RNG == 0) then { P0_RNG = 1 };
P0_fnc_rnd = { P0_RNG = ((P0_RNG * 75) + 74) % 65537; P0_RNG / 65537 };

private _nomI = if (P0_INTENTION == 1) then { "ROMPRE" } else { "ASSAILLIR" };
private _nomR = if (P0_RATIO == 1) then { "1:3" } else { "3:1" };
(format ["PORTE0|OK|monte|%1|graine|%2|intention|%3|ratio|%4|reps|%5",
    P0_VERSION, P0_GRAINE, _nomI, _nomR, P0_REPS]) call P0_LOG;

[] spawn {
    private _nomI = if (P0_INTENTION == 1) then { "ROMPRE" } else { "ASSAILLIR" };
    private _nomR = if (P0_RATIO == 1) then { "1:3" } else { "3:1" };
    private _nA = if (P0_RATIO == 1) then { 4 } else { 12 };
    private _nD = if (P0_RATIO == 1) then { 12 } else { 4 };
    private _fait = 0;

    for "_k" from 0 to (P0_REPS - 1) do {
        private _p = [16000,16000,0];
        for "_t" from 0 to 60 do {
            _p = [] call BIS_fnc_randomPos;
            if ((getTerrainHeightASL _p) > 5) exitWith {};
        };
        private _az = 360 * ([] call P0_fnc_rnd);
        private _dep = [(_p select 0) + 220 * (sin _az), (_p select 1) + 220 * (cos _az), 0];
        private _rall = [(_p select 0) + 620 * (sin _az), (_p select 1) + 620 * (cos _az), 0];

        private _gd = createGroup east; private _ga = createGroup west;
        private _def = []; private _att = [];
        P0_TIRD = 0; P0_TIRA = 0;

        for "_i" from 0 to (_nD - 1) do {
            private _d = _gd createUnit ["O_Soldier_F",
                [(_p select 0) + ((_i % 6) - 3) * 8, (_p select 1) + (floor (_i / 6)) * 8, 0], [], 0, "NONE"];
            _d setSkill 0.5; _d allowFleeing 0; _d setUnitPos "MIDDLE"; _d disableAI "PATH";
            _d setBehaviour "COMBAT"; _d setCombatMode "RED";
            _d addEventHandler ["Fired", { P0_TIRD = P0_TIRD + 1 }];
            _def pushBack _d;
        };
        for "_i" from 0 to (_nA - 1) do {
            private _a = _ga createUnit ["B_Soldier_F",
                [(_dep select 0) + ((_i % 6) - 3) * 6, (_dep select 1) + (floor (_i / 6)) * 6, 0], [], 0, "NONE"];
            _a setSkill 0.5; _a allowFleeing 0; _a setBehaviour "COMBAT"; _a setCombatMode "RED";
            _a addEventHandler ["Fired", { P0_TIRA = P0_TIRA + 1 }];
            _att pushBack _a;
        };
        sleep 3;
        { private _v = _x; { _v reveal [_x, 4] } forEach _def } forEach _att;
        { private _v = _x; { _v reveal [_x, 4] } forEach _att } forEach _def;

        private _but = if (P0_INTENTION == 1) then { _rall } else { _p };
        private _t0 = time; private _pris = 0;
        private _d0 = 0; { _d0 = _d0 + (_x distance2D _p) } forEach _att;
        _d0 = _d0 / (count _att);

        while { (time - _t0) < P0_DUREE } do {
            // ! l ordre est REEMIS : un doMove unique est abandonne des le premier contact
            { if (alive _x) then { _x setSpeedMode "FULL"; _x doMove _but } } forEach _att;
            { if ((alive _x) && {(_x distance2D _p) < 15}) then { _pris = 1 } } forEach _att;
            if ((P0_INTENTION == 0) && {_pris == 1}) exitWith {};
            if (({alive _x} count _att) == 0) exitWith {};
            // ROMPRE aboutit quand le detachement est a plus de 400 m
            if (P0_INTENTION == 1) then {
                private _loin = 0;
                { if ((alive _x) && {(_x distance2D _p) > 400}) then { _loin = _loin + 1 } } forEach _att;
                if ((_loin > 0) && {_loin == ({alive _x} count _att)}) exitWith {};
            };
            sleep 3;
        };

        private _d1 = 0; private _nv = {alive _x} count _att;
        if (_nv > 0) then {
            { if (alive _x) then { _d1 = _d1 + (_x distance2D _p) } } forEach _att;
            _d1 = _d1 / _nv;
        } else { _d1 = -1 };

        (format ["PORTE0|EP|%1|%2|%3|%4|%5|%6|%7|%8|%9|%10",
            _k, _nomI, _nomR, _pris, _nv, count _att,
            ({alive _x} count _def), P0_TIRA, P0_TIRD,
            round _d1]) call P0_LOG;

        { deleteVehicle _x } forEach (_att + _def);
        { if ((count units _x) == 0) then { deleteGroup _x } } forEach allGroups;
        _fait = _fait + 1;
        sleep 2;
    };
    (format ["PORTE0|FINI|%1|graine|%2", _fait, P0_GRAINE]) call P0_LOG;
};
