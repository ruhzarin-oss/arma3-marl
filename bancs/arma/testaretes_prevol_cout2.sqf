// prevol_cout2.sqf — LE COUT, MESURE POUR DE BON.
//
// La mesure precedente annonçait 459 ms par tick alors que l emetteur tourne en production a
// 6,7 ms. Facteur 70 : impossible. La cause est methodologique — je chronometrais dans un
// spawn, donc sous l ORDONNANCEUR SQF, qui decoupe la boucle sur plusieurs images. Le
// chronometre comptait les attentes entre images, pas le calcul.
//
// Ici tout ce qui est chronometre passe par isNil { }, qui force le contexte NON ORDONNANCE
// — le meme que celui du handler EachFrame ou vit le vrai emetteur.
//
// Controle de vraisemblance inclus : la strategie F reproduit la v7 a l identique. Si elle ne
// retombe pas dans l ordre de grandeur des 6,7 ms mesurees en production, la mesure est encore
// fausse et on ne conclut pas.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 10;
    private _base = [1700, 5450, 0];
    private _gE = createGroup east; private _gW = createGroup west;
    HMT_FOULE = [];
    for "_i" from 0 to 259 do {
        private _p = _base vectorAdd [(random 600) - 300, (random 600) - 300, 0];
        private _u = ((if (_i % 2 == 0) then {_gE} else {_gW})
                      createUnit [(if (_i % 2 == 0) then {"O_Soldier_F"} else {"B_Soldier_F"}), _p, [], 0, "NONE"]);
        _u setPosATL _p; _u allowDamage false; _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u setVariable ["hmt_id", _i + 1];
        HMT_FOULE pushBack _u;
    };
    sleep 3;
    (format ["HMT|W2|foule|%1|extension|%2", count HMT_FOULE,
             ("hmt_native" callExtension "version")]) call HMT_LOG;

    HMT_LIRE7 = {
        private _u = _this; private _p = getPosASL _u;
        [(_u getVariable ["hmt_id", -1]),
         (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10, (round ((_p select 2)*10))/10,
         (if (alive _u) then {1} else {0}), 0, 0]
    };
    HMT_LIRE10 = {
        private _u = _this; private _p = getPosASL _u; private _d = eyeDirection _u;
        [(_u getVariable ["hmt_id", -1]),
         (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10, (round ((_p select 2)*10))/10,
         (if (alive _u) then {1} else {0}), 0, 0,
         (round ((((_d select 0) atan2 (_d select 1)) + 360) % 360)),
         (switch (unitPos _u) do { case "UP": {0}; case "MIDDLE": {1}; case "DOWN": {2}; default {3} }), 0]
    };

    // chronometre NON ORDONNANCE : isNil force l execution hors scheduler
    HMT_CHRONO = {
        params ["_bloc", "_tours"];
        private _t = 0;
        isNil {
            private _t0 = diag_tickTime;
            for "_k" from 1 to _tours do { call _bloc };
            _t = (diag_tickTime - _t0) * 1000 / _tours;
        };
        round (_t * 1000) / 1000
    };

    private _T = 30;
    private _r = [];

    // D · lecture seule, sept nombres
    _r pushBack ["D7_lecture7", ([{ { private _v = _x call HMT_LIRE7 } forEach HMT_FOULE }, _T] call HMT_CHRONO)];
    // D10 · lecture seule, dix nombres
    _r pushBack ["D10_lecture10", ([{ { private _v = _x call HMT_LIRE10 } forEach HMT_FOULE }, _T] call HMT_CHRONO)];

    // F · la v7 EXACTE : lecture 7 + concat + decoupage + diag_log  (controle de vraisemblance)
    _r pushBack ["F_v7_exacte", ([{
        private _b = []; private _c = "";
        { private _e = str (_x call HMT_LIRE7);
          if ((count _c) + (count _e) + 1 > 850) then { _b pushBack _c; _c = "" };
          _c = if (_c == "") then { _e } else { _c + "," + _e } } forEach HMT_FOULE;
        _b pushBack _c;
        { diag_log format ["HMT|Z|%1|[%2]", _forEachIndex, _x] } forEach _b;
    }, _T] call HMT_CHRONO)];

    // A · concat seule, dix nombres
    _r pushBack ["A_concat10", ([{
        private _c = "";
        { private _e = str (_x call HMT_LIRE10);
          _c = if (_c == "") then { _e } else { _c + "," + _e } } forEach HMT_FOULE;
    }, _T] call HMT_CHRONO)];

    // B · tableau + joinString, dix nombres
    _r pushBack ["B_join10", ([{
        private _l = [];
        { _l pushBack (str (_x call HMT_LIRE10)) } forEach HMT_FOULE;
        private _s = _l joinString ",";
    }, _T] call HMT_CHRONO)];

    // E · tableau + joinString + UN appel extension
    _r pushBack ["E_join_ext10", ([{
        private _l = [];
        { _l pushBack (str (_x call HMT_LIRE10)) } forEach HMT_FOULE;
        "hmt_native" callExtension ("o|" + (_l joinString ","));
    }, _T] call HMT_CHRONO)];

    // C · un appel extension par entite
    _r pushBack ["C_ext_par_entite", ([{
        { "hmt_native" callExtension ("o|" + (str (_x call HMT_LIRE10))) } forEach HMT_FOULE;
    }, _T] call HMT_CHRONO)];

    // G · lecture RICHE : vingt-cinq grandeurs par homme, pour repondre a « tout prendre »
    _r pushBack ["G_lecture25", ([{
        {
            private _u = _x; private _p = getPosASL _u; private _d = eyeDirection _u;
            private _v = velocity _u; private _hp = getAllHitPointsDamage _u;
            private _z = [(_u getVariable ["hmt_id",-1]),
                (_p select 0),(_p select 1),(_p select 2),(_v select 0),(_v select 1),(_v select 2),
                (alive _u),(damage _u),(getFatigue _u),(getSuppression _u),(unitPos _u),
                (behaviour _u),(combatMode _u),(speedMode _u),(currentCommand _u),
                (lifeState _u),(currentWeapon _u),(_u ammo (currentWeapon _u)),
                (getDir _u),(_d select 0),(_d select 1),(count (magazines _u)),
                (stance _u),(count _hp)];
        } forEach HMT_FOULE;
    }, _T] call HMT_CHRONO)];

    private _s = "";
    { _s = _s + "|" + (_x select 0) + "|" + str (_x select 1) } forEach _r;
    (format ["HMT|W2|resultat%1", _s]) call HMT_LOG;
    "HMT|OK|prevol_cout2|1" call HMT_LOG;
};
"HMT|OK|prevol_cout2_lance|1" call HMT_LOG;
