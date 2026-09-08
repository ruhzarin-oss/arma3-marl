// =====================================================================
// NUIT 1 - L ANCRE B, ET B CONTRE C. Mission entierement scriptee, aucun joueur.
//
// Elle produit DEUX choses :
//   1. l ANCRE : le niveau de B ( 4 fixeurs + 4 assaillants FRONTAUX ), qui servira
//      de reference a tout le reste du programme de certification ;
//   2. B contre C ( 4 fixeurs + 4 debordants ), en ABBA DANS la graine.
//
// TROIS REGLES QUI NE SE NEGOCIENT PAS ( arbitrage Fable, 08/09 ) :
//   . ABBA DANS chaque graine, jamais B puis C : une derive ( FPS, le declin
//     inexplique ) se deguiserait en effet du flanc.
//   . UNE LIGNE PAR EPISODE, avec horodatage, graine, condition, azimut et tirs
//     par camp : c est elle qui permet de separer la stabilite INTRA-graine de
//     l accord INTER-graines. La graine n est PAS une moitie de nuit.
//   . LE BANC DOIT SAVOIR ECHOUER : chaque controle est rendu REUSSI/ECHOUE, et
//     un seul manquant rend l episode REFUSE. " COMPLET n est pas valide. "
//
// Le journal passe par diag_log : le RPT survit a ce qui tue un pont.
// =====================================================================

N1_VERSION = 1;
N1_LOG = { diag_log _this };

N1_GRAINE   = ["N1_GRAINE", 1] call BIS_fnc_getParamValue;
N1_EPISODES = ["N1_EPISODES", 24] call BIS_fnc_getParamValue;
N1_DUREE    = ["N1_DUREE", 300] call BIS_fnc_getParamValue;

// Tirage a nous, pas au moteur : `setRandomSeed` n existe pas dans ce build, et un
// generateur porte reste reproductible sans perturber le hasard interne d Arma -
// que LAMBS doit garder libre pour decider vraiment. Lehmer, module 65537.
N1_RNG = ((N1_GRAINE * 7919) + 104729) % 65537;
if (N1_RNG == 0) then { N1_RNG = 1 };
N1_fnc_rnd = { N1_RNG = ((N1_RNG * 75) + 74) % 65537; N1_RNG / 65537 };

// Azimut d un point par rapport a l axe defendu, ramene dans [0 ; 180].
N1_fnc_azimut = {
    params ["_pos", "_obj", "_axe"];
    private _a = ((_pos select 0) - (_obj select 0)) atan2 ((_pos select 1) - (_obj select 1));
    private _d = (_a - _axe) % 360;
    if (_d < 0) then { _d = _d + 360 };
    if (_d > 180) then { _d = 360 - _d };
    _d
};

(format ["NUIT1|OK|monte|%1|graine|%2|episodes|%3", N1_VERSION, N1_GRAINE, N1_EPISODES]) call N1_LOG;

[] spawn {
    private _fait = 0;
    for "_k" from 0 to (N1_EPISODES - 1) do {

        // ABBA : B C C B, B C C B ... L ordre alterne DANS la graine.
        private _m = _k % 4;
        private _cond = if ((_m == 0) || (_m == 3)) then { "B" } else { "C" };

        // --- un site plat, tire par NOTRE generateur, verifie avant usage -----
        private _p = [16000,16000,0]; private _ok = false;
        for "_t" from 0 to 60 do {
            _p = [] call BIS_fnc_randomPos;
            if (((getTerrainHeightASL _p) > 5) && {(count (nearestObjects [_p, ["House","Building"], 60])) == 0}) exitWith { _ok = true };
        };
        if (!_ok) then { (format ["NUIT1|EP|%1|%2|SITE_REFUSE", _k, _cond]) call N1_LOG };

        private _az = 360 * ([] call N1_fnc_rnd);
        private _dep = [(_p select 0) + 220 * (sin _az), (_p select 1) + 220 * (cos _az), 0];
        // l axe DEFENDU : la direction d ou l assaut arrive, vue depuis l objectif
        private _axeDef = (( (_dep select 0) - (_p select 0) ) atan2 ( (_dep select 1) - (_p select 1) ));

        private _gd = createGroup east; private _ga = createGroup west;
        private _def = []; private _att = [];
        N1_TIRD = 0; N1_TIRA = 0;

        for "_i" from 0 to 3 do {
            private _d = _gd createUnit ["O_Soldier_F", [(_p select 0) + (_i - 2) * 8, _p select 1, 0], [], 0, "NONE"];
            _d setSkill 0.5; _d allowFleeing 0; _d setUnitPos "MIDDLE"; _d disableAI "PATH";
            _d setBehaviour "COMBAT"; _d setCombatMode "RED";
            _d addEventHandler ["Fired", { N1_TIRD = N1_TIRD + 1 }];
            _def pushBack _d;
        };
        for "_i" from 0 to 7 do {
            private _a = _ga createUnit ["B_Soldier_F",
                [(_dep select 0) + (_i % 4) * 6 - 9, (_dep select 1) + (floor (_i / 4)) * 6, 0], [], 0, "NONE"];
            _a setSkill 0.5; _a allowFleeing 0; _a setBehaviour "COMBAT"; _a setCombatMode "RED";
            _a setVariable ["n1_az", -1];
            _a addEventHandler ["Fired", { N1_TIRA = N1_TIRA + 1 }];
            // AZIMUT AU PREMIER COUP RECU : c est la definition du controle de
            // manipulation. Il ne se releve qu une fois, et jamais apres.
            _a addEventHandler ["Hit", {
                params ["_u"];
                if ((_u getVariable ["n1_az", -1]) < 0) then {
                    _u setVariable ["n1_az", [getPosATL _u, N1_OBJ, N1_AXE] call N1_fnc_azimut];
                };
            }];
            _att pushBack _a;
        };
        N1_OBJ = _p; N1_AXE = _axeDef;

        sleep 3;
        { private _v = _x; { _v reveal [_x, 4] } forEach _def } forEach _att;
        { private _v = _x; { _v reveal [_x, 4] } forEach _att } forEach _def;

        // les 4 premiers FIXENT dans les deux conditions : seul l AXE change
        for "_i" from 0 to 3 do {
            private _f = _att select _i;
            _f setUnitPos "DOWN"; _f disableAI "PATH";
        };
        private _flanc = [(_p select 0) + 90 * (sin (_axeDef + 90)), (_p select 1) + 90 * (cos (_axeDef + 90)), 0];
        private _but = if (_cond == "C") then { _flanc } else { _p };

        private _t0 = time; private _pris = 0;
        while { (time - _t0) < N1_DUREE } do {
            for "_i" from 0 to 3 do {
                private _f = _att select _i;
                if (alive _f) then { { if (alive _x) then { _f doTarget _x; _f doFire _x } } forEach _def };
            };
            // ! UN doMove EMIS UNE SEULE FOIS EST ABANDONNE DES LE PREMIER CONTACT
            // en comportement COMBAT ( mesure du 04/09 : 8/8 et 4/4 vivants, rien en
            // 150 s ). On le REEMET, et dans LES DEUX conditions a l identique.
            private _but2 = if ((_cond == "C") && {(time - _t0) <= 45}) then { _flanc } else { _p };
            for "_i" from 4 to 7 do {
                private _m2 = _att select _i;
                if (alive _m2) then { _m2 setSpeedMode "FULL"; _m2 doMove _but2 };
            };
            { if ((alive _x) && {(_x distance2D _p) < 15}) then { _pris = 1 } } forEach _att;
            if (_pris == 1) exitWith {};
            if (({alive _x} count _att) == 0) exitWith {};
            sleep 3;
        };

        // --- l azimut des DEBORDANTS, au premier coup recu -------------------
        private _azs = [];
        for "_i" from 4 to 7 do {
            private _v = (_att select _i) getVariable ["n1_az", -1];
            if (_v >= 0) then { _azs pushBack _v };
        };
        private _azm = -1;
        if ((count _azs) > 0) then {
            _azs sort true;
            _azm = _azs select (floor ((count _azs) / 2));
        };

        private _va = {alive _x} count _att; private _vd = {alive _x} count _def;
        (format ["NUIT1|EP|%1|%2|%3|%4|%5|%6|%7|%8|%9|%10",
            _k, _cond, _pris, _va, _vd, N1_TIRA, N1_TIRD,
            round _azm, count _azs, round (time - _t0)]) call N1_LOG;

        { deleteVehicle _x } forEach (_att + _def);
        { if ((count units _x) == 0) then { deleteGroup _x } } forEach allGroups;
        _fait = _fait + 1;
        sleep 2;
    };
    (format ["NUIT1|FINI|%1|graine|%2", _fait, N1_GRAINE]) call N1_LOG;
};
