// test_aretes4.sqf — le décor mis en travers, POUR DE BON.
//
// v3 a montré que la géométrie est saine : terrain plat (dénivelé 0), ligne de visée à 1,53 m,
// rideau à 3,64 m, dépassement 2,11 m. Et les sondes passent quand même au travers.
//
// La faute est dans MON script, pas dans le moteur : la sonde qui choisissait l orientation
// tirait vers le POINT OÙ EST LE MUR. Elle touchait donc quelle que soit l orientation, et
// n a rien discriminé. J ai retenu dir 90, qui range les panneaux LE LONG de la ligne de vue.
//
// Ici on essaie chaque orientation en tirant LA VRAIE LIGNE A→B2, et on garde celle qui
// bloque. Si aucune ne bloque, on passe à un bâtiment massif — et si ça ne bloque toujours
// pas, alors seulement la sonde est en cause.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 8;
    private _base = [1700, 5450, 0];
    private _milieu = _base vectorAdd [0, -25, 0];
    private _posB2 = _base vectorAdd [0, -50, 0];

    private _gE = createGroup east; private _gW = createGroup west;
    private _A  = _gE createUnit ["O_Soldier_F", _base,  [], 0, "NONE"]; _A  setPosATL _base;
    private _B1 = _gW createUnit ["B_Soldier_F", (_base vectorAdd [50,0,0]), [], 0, "NONE"];
    _B1 setPosATL (_base vectorAdd [50,0,0]);
    private _B2 = _gW createUnit ["B_Soldier_F", _posB2, [], 0, "NONE"]; _B2 setPosATL _posB2;
    { removeAllWeapons _x; _x allowDamage false; _x disableAI "PATH"; _x disableAI "AUTOCOMBAT";
      _x setBehaviour "COMBAT"; _x setUnitPos "UP" } forEach [_A, _B1, _B2];
    _A setDir 180;
    sleep 3;

    // LA sonde de référence : la vraie ligne, les deux soldats ignorés, tout le reste compté.
    // ⟨v3 : sans ignorer les soldats on compte 2 intersections partout — ce sont eux.⟩
    HMT_BLOQUE = {
        params ["_o", "_c"];
        count (lineIntersectsSurfaces [eyePos _o, aimPos _c, _o, _c, true, 16, "GEOM", "NONE"])
    };

    private _poser = {
        params ["_dir", "_rangs"];
        private _l = [];
        for "_r" from 0 to (_rangs - 1) do {
            {
                private _m = createVehicle ["Land_CncWall4_F", [0,0,0], [], 0, "CAN_COLLIDE"];
                _m setDir _dir;
                _m setPosATL [(_milieu select 0) + _x, (_milieu select 1), _r * 1.8];
                _l pushBack _m;
            } forEach [-8, -4, 0, 4, 8];
        };
        _l
    };

    // ---------- on essaie les orientations SUR LA VRAIE LIGNE ----------
    private _murs = []; private _garde = -1; private _best = 0;
    {
        private _d = _x;
        { deleteVehicle _x } forEach _murs;
        _murs = [_d, 2] call _poser;
        sleep 1;
        private _nb = [_A, _B2] call HMT_BLOQUE;
        private _nbTemoin = [_A, _B1] call HMT_BLOQUE;      // le dégagé doit rester à 0
        (format ["HMT|G|essai|dir|%1|inter_vers_B2|%2|inter_vers_B1_degage|%3", _d, _nb, _nbTemoin]) call HMT_LOG;
        if (_nb > _best) then { _best = _nb; _garde = _d };
    } forEach [0, 45, 90, 135];

    { deleteVehicle _x } forEach _murs; _murs = [];

    if (_garde < 0) then {
        // aucun mur ne bloque : on passe à un objet massif, indiscutable
        "HMT|G|repli|batiment" call HMT_LOG;
        private _b = createVehicle ["Land_Cargo_HQ_V1_F", [0,0,0], [], 0, "CAN_COLLIDE"];
        _b setPosATL [(_milieu select 0), (_milieu select 1), 0];
        _murs = [_b];
        sleep 2;
        (format ["HMT|G|batiment|inter_vers_B2|%1", [_A, _B2] call HMT_BLOQUE]) call HMT_LOG;
    } else {
        _murs = [_garde, 2] call _poser;
        sleep 2;
    };

    (format ["HMT|OK|decor|1|dir_retenue|%1|inter_B2|%2|inter_B1|%3",
             _garde, [_A, _B2] call HMT_BLOQUE, [_A, _B1] call HMT_BLOQUE]) call HMT_LOG;

    // ---------- les sondes, sur un décor dont on SAIT qu il est en travers ----------
    HMT_S = {
        params ["_o", "_c"];
        private _r = [];
        {
            private _i = lineIntersectsSurfaces [eyePos _o, aimPos _c, _o, _c, true, 1,
                                                 (_x select 0), (_x select 1)];
            _r pushBack (if (count _i == 0) then {1} else {0});
        } forEach [["VIEW","FIRE"], ["GEOM","NONE"], ["FIRE","NONE"], ["VIEW","NONE"]];
        _r pushBack ([_o, _c] call HMT_BLOQUE);
        _r pushBack (round (([objNull, "VIEW"] checkVisibility [eyePos _o, aimPos _c]) * 100) / 100);
        _r
    };

    "HMT|OK|scene4|1" call HMT_LOG;
    private _n = 0;
    while { _n < 40 } do {
        _n = _n + 1;
        {
            private _B = _x select 0; private _s = [_A, _B] call HMT_S;
            private _tk = _A targetKnowledge _B;
            (format ["HMT|AR4|%1|A|%2|k|%3|vu|%4|viewfire|%5|geom|%6|fire|%7|viewnone|%8|nbinter|%9|checkvis|%10",
                     _n, (_x select 1), (round ((_A knowsAbout _B)*100))/100,
                     (if ((count _tk) > 1 && {_tk select 1}) then {1} else {0}),
                     (_s select 0), (_s select 1), (_s select 2), (_s select 3),
                     (_s select 4), (_s select 5)]) call HMT_LOG;
        } forEach [[_B1,"B1_degage"], [_B2,"B2_COUVERT"]];
        sleep 2;
    };
    (format ["HMT|OK|aretes4|1|ticks|%1", _n]) call HMT_LOG;
};
"HMT|OK|test_aretes4|1" call HMT_LOG;
