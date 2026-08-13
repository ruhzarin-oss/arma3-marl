// banc150b.sqf — LE BANC INSTRUMENTE. Cinq bras, dont L'AGENT.
//
// ⟨Fable, 04/08 : « Tu annonces 20 configurations x 4 bras et ta table montre TROIS lignes.
//  Ou est l'agent ? A ce jour, l'agent n'a JAMAIS ete mesure par un instrument valide.
//  Toute philosophie de registre deposee avant cette ligne de table est prematuree. »⟩
//
// TROIS DEFAUTS DU BANC PRECEDENT, CORRIGES ICI
//
//  1. L'AGENT N'Y ETAIT PAS. Quatre bras, aucun n'etait lui. On mesurait des chemins
//     calcules contre des chemins calcules. Il est ici, et c'est le seul bras qui compte.
//
//  2. LA POSTURE ETAIT FORCEE DEBOUT. Le banc precedent ecrivait setUnitPos "UP" : il
//     eteignait le repertoire dans l'instrument de mesure, alors qu'on a MESURE que le
//     couche est invisible au-dela de 120 m ⟨banc couvert, 03/08, 52 essais⟩. Chaque point
//     porte desormais sa posture, et elle est appliquee.
//
//  3. LA METRIQUE ETAIT BIAISEE CONTRE LES CHEMINS LONGS. On relevait la distance a
//     l'objectif au moment du reperage : un chemin qui serpente passe l'essentiel de ses
//     points loin de l'objectif, donc a hasard EGAL il enregistre mecaniquement une
//     distance plus grande. Le « 141 contre 78 » du 04/08 n'etait pas interpretable.
//     On releve maintenant la SURVIE AUX JALONS : etait-il encore invisible en franchissant
//     120, 90, 60 puis 40 m ? Un jalon est une position, pas une duree : aucun chemin n'est
//     avantage par sa forme.
//
// LA TELEMETRIE QUI MANQUAIT — LE REGARD, PAS LE CORPS
//   On avait mesure la derive de POSITION des defenseurs (0,1 m) et jamais leur REGARD.
//   Or si les tetes balaient, la carte d'ombre statique ne veut plus rien dire, et l'effet
//   de duree s'explique tout seul : cone balayant x temps = hasard cumule.
//   getDir rend le cap du CORPS, qu'on force toutes les 0,5 s — le mesurer ne prouverait
//   rien. eyeDirection rend la direction du REGARD. C'est elle qu'on releve, a 1 Hz.
//
// CE QUI FERAIT ECHOUER LA MESURE — ecrit avant :
//   P1 PRESENCE  : la ligne droite doit etre vue avant 40 m dans >= 16 configurations.
//   P2 NUL       : droite et droite_bis doivent donner le meme verdict de survie sur >= 18.
//   P3 AGENT     : l'agent bat la droite en survie appariee sur >= 15 configurations sur 20.
//                  ⟨critere ecrit AVANT le run. L'ancien seuil de +25 % est mort avec le
//                   signe inverse qu'on lui a trouve le 04/08.⟩
//   P4 PLAFOND   : l'oracle libre doit faire au moins aussi bien que la droite. Sinon le
//                  chemin calcule ne vaut rien et le plafond n'en est pas un.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
call compile preprocessFileLineNumbers "donnees_banc150b.sqf";
if (isNil "HMT_DATA") exitWith { "HMT|B150B|ECHEC|donnees_non_chargees" call HMT_LOG };
if (!(HMT_DATA isEqualType [])) exitWith { "HMT|B150B|ECHEC|donnees_mal_formees" call HMT_LOG };
HMT_JALONS = [120, 90, 60, 40];
(format ["HMT|B150B|debut|%1|configs|jalons|%2", count HMT_DATA, str HMT_JALONS]) call HMT_LOG;

[] spawn {
    sleep 20;

    private _base = []; private _tol = 0;
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 4000 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        {
                            private _q = _c vectorAdd _x;
                            if (surfaceIsWater _q) then { _ok = false };
                            if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                            if (count (nearestTerrainObjects [_q, ["TREE","HOUSE"], 20]) > 0) then { _ok = false };
                        } forEach [[0,0,0],[155,0,0],[-155,0,0],[0,155,0],[0,-155,0],
                                   [110,110,0],[-110,-110,0],[110,-110,0],[-110,110,0],
                                   [75,0,0],[0,75,0],[-75,0,0],[0,-75,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [12, 20, 30, 45];
    if (count _base == 0) exitWith { "HMT|B150B|ECHEC|aucun_terrain" call HMT_LOG };
    (format ["HMT|B150B|terrain|%1|%2|denivele|%3", round (_base select 0),
             round (_base select 1), _tol]) call HMT_LOG;

    HMT_SU = { private _k = 0; { private _v = _x knowsAbout _this; if (_v > _k) then { _k = _v } } forEach HMT_DEF; _k };
    HMT_POSTURE = { ["UP","MIDDLE","DOWN"] select _this };

    // ---------- rejouer un bras ----------
    HMT_REJOUE = {
        params ["_lib", "_pts", "_cfg"];
        private _g = createGroup west;
        private _q0 = _pts select 0;
        private _p0 = _base vectorAdd [_q0 select 0, _q0 select 1, 0];
        private _a = _g createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
        _a setPosATL _p0; _a allowDamage false; removeAllWeapons _a;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT";
        _a setUnitPos ((_q0 select 2) call HMT_POSTURE);   // LA POSTURE VIENT DES DONNEES
        sleep 2;

        private _k = 0;
        private _jal = [];                 // survie a chaque jalon : 1 = encore invisible
        { _jal pushBack -1 } forEach HMT_JALONS;
        private _dPrec = 999;
        private _nCouche = 0;
        {
            private _p = _base vectorAdd [_x select 0, _x select 1, 0];
            _a setPosATL _p;
            _a setUnitPos ((_x select 2) call HMT_POSTURE);
            if ((_x select 2) == 2) then { _nCouche = _nCouche + 1 };
            sleep 1.2;
            private _v = _a call HMT_SU;
            if (_v > _k) then { _k = _v };
            private _d = sqrt (((_x select 0)^2) + ((_x select 1)^2));
            // SURVIE AUX JALONS : au PREMIER franchissement de chaque jalon, est-il encore
            // invisible ? Un jalon est une position, pas une duree.
            {
                private _i = _forEachIndex;
                if (_d <= _x && _dPrec > _x && (_jal select _i) < 0) then {
                    _jal set [_i, (if (_k < 1.5) then {1} else {0})];
                };
            } forEach HMT_JALONS;
            _dPrec = _d;
        } forEach _pts;

        private _fin = (_pts select ((count _pts) - 1));
        private _reste = round (sqrt (((_fin select 0)^2) + ((_fin select 1)^2)));
        (format ["HMT|B150B|essai|%1|%2|know|%3|reste|%4|jalons|%5|points|%6|couche|%7",
                 _cfg, _lib, (round (_k*100))/100, _reste, str _jal,
                 count _pts, _nCouche]) call HMT_LOG;
        deleteVehicle _a; deleteGroup _g;
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 4;
    };

    private _n = 0;
    {
        _n = _n + 1;
        private _defs = _x select 0;
        private _bras = _x select 1;

        private _gD = createGroup east;
        HMT_DEF = [];
        {
            private _p = _base vectorAdd [_x select 0, _x select 1, 0];
            private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u allowDamage false; removeAllWeapons _u;
            _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "ANIM";
            _u setBehaviour "SAFE"; _u setUnitPos "UP";
            _u setDir (_x select 2);
            _u setVariable ["cap", _x select 2];
            _u setVariable ["voulu", [_x select 0, _x select 1]];
            HMT_DEF pushBack _u;
        } forEach _defs;
        private _garde = [] spawn { while { true } do {
            { _x setDir (_x getVariable ["cap", 0]) } forEach HMT_DEF; sleep 0.5 } };

        // LA TELEMETRIE DU REGARD, a 1 Hz. eyeDirection, pas getDir : le cap du corps est
        // force toutes les 0,5 s, le mesurer ne prouverait rien. Le regard, lui, est libre.
        HMT_CFG = _n;
        private _oeil = [] spawn {
            while { true } do {
                private _emax = 0; private _somme = 0;
                {
                    private _e = eyeDirection _x;
                    private _az = (((_e select 0) atan2 (_e select 1)) + 360) % 360;
                    private _c = _x getVariable ["cap", 0];
                    private _ec = abs ((_az - _c + 180) % 360 - 180);
                    if (_ec > _emax) then { _emax = _ec };
                    _somme = _somme + _ec;
                } forEach HMT_DEF;
                (format ["HMT|B150B|regard|%1|ecart_max|%2|ecart_moyen|%3|n|%4", HMT_CFG,
                         round _emax, round (_somme / ((count HMT_DEF) max 1)),
                         count HMT_DEF]) call HMT_LOG;
                sleep 1;
            };
        };
        sleep 4;

        private _derive = 0;
        {
            private _v = _x getVariable ["voulu", [0,0]];
            private _reel = [(getPosATL _x select 0) - (_base select 0),
                             (getPosATL _x select 1) - (_base select 1)];
            private _e = sqrt ((((_reel select 0)-(_v select 0))^2) + (((_reel select 1)-(_v select 1))^2));
            if (_e > _derive) then { _derive = _e };
        } forEach HMT_DEF;
        (format ["HMT|B150B|config|%1|defenseurs|%2|derive_max|%3|caps|%4", _n, count HMT_DEF,
                 (round (_derive*10))/10, str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

        { [_x select 0, _x select 1, _n] call HMT_REJOUE } forEach _bras;

        terminate _oeil; terminate _garde;
        { deleteVehicle _x } forEach HMT_DEF;
        deleteGroup _gD;
        sleep 3;
    } forEach HMT_DATA;

    "HMT|B150B|TERMINE|1" call HMT_LOG;
};
