// prevol8.sqf — PRÉ-VOL de la capture v8. Rien n est deploye avant que ceci passe.
//
// Deux commandes de la v8 n ont jamais ete testees : eyeDirection, et le handler FiredMan
// dont je SUPPOSE qu il livre la cible en 8e parametre. ⟨29/07 : une commande absente tue
// le gestionnaire EN SILENCE et emporte tout le script. currentTarget en est mort.⟩
//
// On teste aussi le COUT a densite reelle : Battle Lines tient 264 entites, et l emetteur
// v7 coutait deja 6,7 ms/tick pour SEPT nombres. La v8 en emet DIX.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

// ---------- 1. EXISTENCE, par le catalogue du moteur ----------
private _toutes = supportInfo "";
private _cherche = {
    private _c = toLower _this; private _t = false;
    { private _l = toLower _x;
      if ((_l find (":" + _c + " ")) >= 0 || (_l find (" " + _c + " ")) >= 0
          || _l == ("n:" + _c) || _l == ("u:" + _c)) exitWith { _t = true };
    } forEach _toutes;
    _t
};
{ (format ["HMT|X|cmd|%1|%2", _x, (if (_x call _cherche) then {1} else {0})]) call HMT_LOG;
} forEach ["eyeDirection", "assignedTarget", "unitPos", "getSuppression", "nearTargets",
           "targetKnowledge", "aimedAtTarget", "getDir", "vectorDir"];
"HMT|OK|prevol_existence|1" call HMT_LOG;

[] spawn {
    sleep 10;
    private _base = [1700, 5450, 0];

    // ---------- 2. FiredMan livre-t-il vraiment une cible ? ----------
    // On arme un tireur, on lui donne un ennemi, et on IMPRIME la forme brute de _this.
    private _gE = createGroup east; private _gW = createGroup west;
    private _T = _gE createUnit ["O_Soldier_F", _base, [], 0, "NONE"]; _T setPosATL _base;
    private _C = _gW createUnit ["B_Soldier_F", (_base vectorAdd [40,0,0]), [], 0, "NONE"];
    _C setPosATL (_base vectorAdd [40,0,0]);
    _C allowDamage false; _C disableAI "PATH"; removeAllWeapons _C;
    _T disableAI "PATH"; _T setBehaviour "COMBAT";

    _T addEventHandler ["Fired", {
        (format ["HMT|X|Fired|nb_params|%1|types|%2", count _this,
                 (_this apply { typeName _x }) joinString ","]) call HMT_LOG;
    }];
    _T addEventHandler ["FiredMan", {
        (format ["HMT|X|FiredMan|nb_params|%1|types|%2", count _this,
                 (_this apply { typeName _x }) joinString ","]) call HMT_LOG;
        // que vaut le 8e parametre, celui que je prenais pour la cible ?
        if ((count _this) > 7) then {
            private _h = _this select 7;
            (format ["HMT|X|FiredMan_p8|type|%1|estUnite|%2|estNull|%3|nom|%4",
                     typeName _h,
                     (if (_h isEqualType objNull && {_h isKindOf 'CAManBase'}) then {1} else {0}),
                     (if (_h isEqualType objNull && {isNull _h}) then {1} else {0}),
                     (if (_h isEqualType objNull) then { typeOf _h } else { str _h })]) call HMT_LOG;
        };
        // et la cible assignee, elle ?
        private _at = assignedTarget (_this select 0);
        (format ["HMT|X|assignedTarget|estNull|%1|nom|%2",
                 (if (isNull _at) then {1} else {0}),
                 (if (isNull _at) then {"-"} else { typeOf _at })]) call HMT_LOG;
    }];
    sleep 25;

    // ---------- 3. eyeDirection rend-il quelque chose d exploitable ? ----------
    private _ed = eyeDirection _T;
    (format ["HMT|X|eyeDirection|type|%1|taille|%2|valeur|%3|azimut|%4",
             typeName _ed, count _ed, str _ed,
             round ((((_ed select 0) atan2 (_ed select 1)) + 360) % 360)]) call HMT_LOG;
    _T setDir 90; sleep 2;
    private _e2 = eyeDirection _T;
    (format ["HMT|X|eyeDirection_apres_setDir90|azimut|%1",
             round ((((_e2 select 0) atan2 (_e2 select 1)) + 360) % 360)]) call HMT_LOG;
    "HMT|OK|prevol_commandes|1" call HMT_LOG;

    // ---------- 4. LE COUT, a densite reelle ----------
    // Battle Lines tient 264 entites. On en fabrique 260 immobiles et on chronometre
    // l emetteur v7 (sept nombres) puis v8 (dix nombres), sur les MEMES unites.
    private _foule = [];
    for "_i" from 0 to 259 do {
        private _g = if (_i % 2 == 0) then {_gE} else {_gW};
        private _p = _base vectorAdd [(random 600) - 300, (random 600) - 300, 0];
        private _u = _g createUnit [(if (_i % 2 == 0) then {"O_Soldier_F"} else {"B_Soldier_F"}),
                                    _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false; _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u setVariable ["hmt_id", _i + 1];
        _foule pushBack _u;
    };
    sleep 3;
    (format ["HMT|X|foule|%1", count _foule]) call HMT_LOG;

    private _mesure = {
        params ["_liste", "_riche", "_tours"];
        private _t0 = diag_tickTime;
        private _nCar = 0;
        for "_k" from 1 to _tours do {
            private _cour = "";
            {
                private _u = _x; private _p = getPosASL _u;
                private _e = if (_riche) then {
                    private _ed = eyeDirection _u;
                    str [(_u getVariable ["hmt_id", -1]),
                         (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10,
                         (round ((_p select 2)*10))/10, (if (alive _u) then {1} else {0}),
                         0, 0, (round ((((_ed select 0) atan2 (_ed select 1)) + 360) % 360)),
                         (switch (unitPos _u) do { case "UP": {0}; case "MIDDLE": {1};
                                                   case "DOWN": {2}; default {3} }), 0]
                } else {
                    str [(_u getVariable ["hmt_id", -1]),
                         (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10,
                         (round ((_p select 2)*10))/10, (if (alive _u) then {1} else {0}), 0, 0]
                };
                _cour = _cour + _e;
            } forEach _liste;
            _nCar = count _cour;
        };
        [((diag_tickTime - _t0) * 1000 / _tours), _nCar]
    };

    private _v7 = [_foule, false, 20] call _mesure;
    private _v8 = [_foule, true,  20] call _mesure;
    (format ["HMT|X|cout|v7_ms|%1|v8_ms|%2|surcout_pct|%3|car_v7|%4|car_v8|%5",
             (round ((_v7 select 0) * 100)) / 100, (round ((_v8 select 0) * 100)) / 100,
             (round (((_v8 select 0) / (_v7 select 0) - 1) * 100)),
             (_v7 select 1), (_v8 select 1)]) call HMT_LOG;

    // combien de morceaux a 700 caracteres, et donc combien de lignes par tick ?
    (format ["HMT|X|morceaux|v8|%1|pour|%2|entites",
             (ceil ((_v8 select 1) / 700)), count _foule]) call HMT_LOG;

    // ---------- 5. isolation de chaque lecture ----------
    private _chrono = {
        params ["_liste", "_bloc", "_tours"];
        private _t0 = diag_tickTime;
        for "_k" from 1 to _tours do { { [_x] call _bloc } forEach _liste };
        ((diag_tickTime - _t0) * 1000 / _tours)
    };
    {
        private _nom = _x select 0; private _b = _x select 1;
        (format ["HMT|X|bloc|%1|ms|%2", _nom,
                 (round (([_foule, _b, 20] call _chrono) * 100)) / 100]) call HMT_LOG;
    } forEach [
        ["getPosASL",    { getPosASL (_this select 0) }],
        ["eyeDirection", { eyeDirection (_this select 0) }],
        ["unitPos",      { unitPos (_this select 0) }],
        ["alive",        { alive (_this select 0) }],
        ["getVariable",  { (_this select 0) getVariable ["hmt_id", -1] }],
        ["str_concat",   { str [1,2.5,3.5,4.5,1,0,0,180,0,0] }]
    ];
    "HMT|OK|prevol_cout|1" call HMT_LOG;
};
"HMT|OK|prevol8|1" call HMT_LOG;
