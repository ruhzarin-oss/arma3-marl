// test_aretes6.sqf — L OBSERVATEUR SEUL.
//
// v5 : B2 est derrière le rideau (vue geometrique 0 %, visibilite 0,00) et pourtant
// knowsAbout vaut 4,00 et la cible est « vue » 97 % du temps. Une seule explication tient :
// C1, camarade de camp place a l ouest, voit B2 par le cote et partage l information.
//
// Si c est vrai, knowsAbout n est pas une perception individuelle mais une connaissance de
// GROUPE — et une arete A->B ne dit pas « A voit B » mais « le camp de A sait ou est B ».
// Ce n est pas un detail : ca change ce que l arete SIGNIFIE dans le corpus.
//
// Ici l observateur est SEUL de son camp. Meme decor, memes distances, aucun camarade.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 8;
    private _base   = [1700, 5450, 0];
    private _milieu = _base vectorAdd [0, -25, 0];

    // le decor d abord, personne ne doit voir la cible avant qu elle soit couverte
    private _murs = [];
    for "_r" from 0 to 1 do {
        {
            private _m = createVehicle ["Land_CncWall4_F", [0,0,0], [], 0, "CAN_COLLIDE"];
            _m setDir 0;
            _m setPosATL [(_milieu select 0) + _x, (_milieu select 1), _r * 1.8];
            _murs pushBack _m;
        } forEach [-8, -4, 0, 4, 8];
    };
    sleep 2;

    private _gE = createGroup east; private _gW = createGroup west;
    private _A = _gE createUnit ["O_Soldier_F", _base, [], 0, "NONE"]; _A setPosATL _base;

    // AUCUN camarade : le groupe EAST ne contient que l observateur
    private _cibles = [];
    {
        private _p = _base vectorAdd (_x select 0);
        private _u = _gW createUnit ["B_Soldier_F", _p, [], 0, "NONE"]; _u setPosATL _p;
        _cibles pushBack [_u, (_x select 1)];
    } forEach [
        [[50, 0, 0],  "B1_degage_50m"],
        [[0, -50, 0], "B2_COUVERT_50m"],
        [[0, 300, 0], "B3_degage_300m"]
    ];

    { removeAllWeapons _x; _x allowDamage false; _x disableAI "PATH"; _x disableAI "AUTOCOMBAT";
      _x setBehaviour "COMBAT"; _x setUnitPos "UP" } forEach ([_A] + (_cibles apply { _x select 0 }));
    _A setDir 0;
    sleep 2;

    (format ["HMT|G|seul|effectif_camp_observateur|%1", count (units _gE)]) call HMT_LOG;
    "HMT|OK|scene6|1" call HMT_LOG;

    private _n = 0;
    while { _n < 90 } do {
        _n = _n + 1;
        {
            private _B = _x select 0;
            private _i = lineIntersectsSurfaces [eyePos _A, aimPos _B, _A, _B, true, 1, "VIEW", "FIRE"];
            private _tk = _A targetKnowledge _B;
            (format ["HMT|AR6|%1|A|%2|k|%3|los|%4|vis|%5|vu|%6",
                     _n, (_x select 1), (round ((_A knowsAbout _B) * 100) / 100),
                     (if (count _i == 0) then {1} else {0}),
                     (round (([objNull,"VIEW"] checkVisibility [eyePos _A, aimPos _B]) * 100) / 100),
                     (if ((count _tk) > 1 && {_tk select 1}) then {1} else {0})]) call HMT_LOG;
        } forEach _cibles;
        sleep 2;
    };
    (format ["HMT|OK|aretes6|1|ticks|%1", _n]) call HMT_LOG;
};
"HMT|OK|test_aretes6|1" call HMT_LOG;
