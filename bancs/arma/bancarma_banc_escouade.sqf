// banc_escouade.sqf — LA MANOEUVRE REND-ELLE A PLUSIEURS CE QU'ELLE NE REND PAS SEUL ?
//
// LA FAILLE QUE CE BANC CORRIGE. J'ai extrait une manoeuvre qui n'existe qu'A PLUSIEURS,
// puis reproche a UN HOMME SEUL de ne pas l'executer. Tous les succes du projet sont
// collectifs ; l'A/B qui a tout fonde — le flanc paie +12,3 points sur 1324 engagements —
// etait mesure A DEUX AXES : quelqu'un FIXAIT pendant que l'autre manoeuvrait.
// Un homme seul qui contourne ne fixe personne. Il marche plus longtemps sous les yeux
// adverses, et c'est tout. ⟨banc solo : l'oracle a 105 points marque 0 sur 4⟩
//
// CINQ BRAS, memes configurations, de 150 m a 40 m :
//   solo           1 homme par le flanc                 le temoin deja mesure
//   bloc_1axe      6 hommes, tout droit                 l'escouade SANS manoeuvre
//   deux_axes      3 fixent de face + 3 par le flanc    la manoeuvre complete
//   flanc_seul     3 hommes par le flanc, SANS appui    LE CONTROLE DECISIF
//   deux_axes_bis  rejeu de deux_axes                   CONTROLE NUL
//
// Le quatrieme bras tranche : si le flanc reussit AUSSI BIEN sans base de feu, la fixation
// n'explique rien et l'analyse tombe.
//
// LES CAPS DES DEFENSEURS NE SONT PLUS VERROUILLES — et c'est indispensable.
// Tous les bancs precedents forcaient setDir toutes les 0,5 s. C'etait juste pour mesurer
// la perception d'un homme seul ⟨un cap suppose avait INVERSE une conclusion le 03/08⟩.
// Mais FIXER, c'est attirer les regards : verrouiller les caps ETEINT le mecanisme meme
// qu'on veut mesurer. Ils sont donc LIBRES, et releves a 1 Hz.
// ⟨le controle nul est deja acquis : sans approchant, eyeDirection ne bouge pas d'un degre.
//  2063 releves du banc solo, ecart median 0°, maximum 0°.⟩
//
// CE QU'ON NOTE : la survie du groupe MANOEUVRANT aux jalons 120 / 90 / 60 / 40 m.
// Un groupe est repere des qu'UN de ses hommes l'est ⟨knowsAbout est de CAMP⟩. On releve
// aussi combien d'hommes sont vus, et ce que devient le groupe FIXANT — se faire voir est
// son role, et s'il n'y arrive pas, le bras ne teste rien.
//
// CE QUI FERAIT ECHOUER LA MESURE — ecrit avant :
//   P1 PRESENCE  bloc_1axe doit etre repere
//   P2 NUL       deux_axes et deux_axes_bis doivent donner le meme verdict
//   P3 FIXATION  le flanc de deux_axes doit survivre a PLUS de jalons que flanc_seul
//   P4 COLLECTIF deux_axes doit battre solo ET bloc_1axe
//   P5 REGARDS   si les caps ne bougent JAMAIS malgre une base de feu visible, le mecanisme
//                de fixation n'existe pas SANS TIR. Ce n'est pas une refutation : c'est
//                qu'il faut des armes, et il faudra le dire au lieu de conclure.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
call compile preprocessFileLineNumbers "donnees_escouade.sqf";
if (isNil "HMT_DATA") exitWith { "HMT|ESC|ECHEC|donnees_non_chargees" call HMT_LOG };
if (!(HMT_DATA isEqualType [])) exitWith { "HMT|ESC|ECHEC|donnees_mal_formees" call HMT_LOG };
HMT_JALONS = [120, 90, 60, 40];
(format ["HMT|ESC|debut|%1|configs|jalons|%2", count HMT_DATA, str HMT_JALONS]) call HMT_LOG;

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
                        } forEach [[0,0,0],[160,0,0],[-160,0,0],[0,160,0],[0,-160,0],
                                   [113,113,0],[-113,-113,0],[113,-113,0],[-113,113,0],
                                   [75,0,0],[0,75,0],[-75,0,0],[0,-75,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [12, 20, 30, 45];
    if (count _base == 0) exitWith { "HMT|ESC|ECHEC|aucun_terrain" call HMT_LOG };
    (format ["HMT|ESC|terrain|%1|%2|denivele|%3", round (_base select 0),
             round (_base select 1), _tol]) call HMT_LOG;

    // ce que le camp sait d'un GROUPE : le maximum sur ses hommes
    HMT_SU_GRP = {
        private _k = 0;
        { private _u = _x; { private _v = _x knowsAbout _u; if (_v > _k) then { _k = _v } } forEach HMT_DEF } forEach _this;
        _k
    };

    // ---------- rejouer un bras : TOUS les hommes avancent ENSEMBLE ----------
    HMT_REJOUE = {
        params ["_lib", "_groupes", "_cfg"];
        private _gW = createGroup west;
        private _unites = [];     // [role, [unites], [trajets]]
        private _nmax = 0;
        {
            private _role = _x select 0;
            private _traj = _x select 1;
            private _us = [];
            {
                private _p0 = _base vectorAdd [(_x select 0) select 0, (_x select 0) select 1, 0];
                private _a = _gW createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
                _a setPosATL _p0; _a allowDamage false; removeAllWeapons _a;
                _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a setUnitPos "UP";
                _us pushBack _a;
                if (count _x > _nmax) then { _nmax = count _x };
            } forEach _traj;
            _unites pushBack [_role, _us, _traj];
        } forEach _groupes;
        sleep 2;

        private _man = [];  private _fix = [];  private _trajMan = [];
        { if ((_x select 0) == "M") then { _man = _x select 1; _trajMan = _x select 2 }
          else { _fix append (_x select 1) } } forEach _unites;

        private _jal = []; { _jal pushBack -1 } forEach HMT_JALONS;
        private _kMan = 0; private _kFix = 0; private _dPrec = 999;
        private _vusMan = 0;

        for "_t" from 0 to (_nmax - 1) do {
            {
                private _us = _x select 1; private _tr = _x select 2;
                {
                    private _h = _tr select _forEachIndex;
                    private _i = (_t min ((count _h) - 1));
                    private _q = _h select _i;
                    _x setPosATL (_base vectorAdd [_q select 0, _q select 1, 0]);
                } forEach _us;
            } forEach _unites;
            sleep 1.2;

            private _v = _man call HMT_SU_GRP;
            if (_v > _kMan) then { _kMan = _v };
            if (count _fix > 0) then {
                private _w = _fix call HMT_SU_GRP;
                if (_w > _kFix) then { _kFix = _w };
            };
            // distance du CENTRE du groupe manoeuvrant a l'objectif
            private _sx = 0; private _sy = 0;
            {
                private _h = _trajMan select _forEachIndex;
                private _q = _h select (_t min ((count _h) - 1));
                _sx = _sx + (_q select 0); _sy = _sy + (_q select 1);
            } forEach _man;
            private _d = sqrt (((_sx/(count _man))^2) + ((_sy/(count _man))^2));
            {
                private _i = _forEachIndex;
                if (_d <= _x && _dPrec > _x && (_jal select _i) < 0) then {
                    _jal set [_i, (if (_kMan < 1.5) then {1} else {0})];
                };
            } forEach HMT_JALONS;
            _dPrec = _d;
        };
        { private _u = _x; private _b = 0;
          { private _z = _x knowsAbout _u; if (_z > _b) then { _b = _z } } forEach HMT_DEF;
          if (_b >= 1.5) then { _vusMan = _vusMan + 1 } } forEach _man;

        (format ["HMT|ESC|essai|%1|%2|man|%3|fix|%4|jalons|%5|vus|%6|sur|%7|pas|%8",
                 _cfg, _lib, (round (_kMan*100))/100, (round (_kFix*100))/100,
                 str _jal, _vusMan, count _man, _nmax]) call HMT_LOG;

        { { deleteVehicle _x } forEach (_x select 1) } forEach _unites;
        deleteGroup _gW;
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 5;
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
            _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
            // PAS de disableAI "ANIM", PAS de garde sur setDir : les regards sont LIBRES.
            // C'est la difference avec tous les bancs precedents, et c'est le point du banc.
            _u setBehaviour "SAFE"; _u setUnitPos "UP";
            _u setDir (_x select 2);
            _u setVariable ["cap0", _x select 2];
            HMT_DEF pushBack _u;
        } forEach _defs;

        HMT_CFG = _n;
        private _oeil = [] spawn {
            while { true } do {
                private _emax = 0; private _somme = 0;
                {
                    private _e = eyeDirection _x;
                    private _az = (((_e select 0) atan2 (_e select 1)) + 360) % 360;
                    private _c = _x getVariable ["cap0", 0];
                    private _ec = abs ((_az - _c + 180) % 360 - 180);
                    if (_ec > _emax) then { _emax = _ec };
                    _somme = _somme + _ec;
                } forEach HMT_DEF;
                (format ["HMT|ESC|regard|%1|ecart_max|%2|ecart_moyen|%3|n|%4", HMT_CFG,
                         round _emax, round (_somme / ((count HMT_DEF) max 1)),
                         count HMT_DEF]) call HMT_LOG;
                sleep 1;
            };
        };
        sleep 4;
        (format ["HMT|ESC|config|%1|defenseurs|%2|caps|%3", _n, count HMT_DEF,
                 str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

        { [_x select 0, _x select 1, _n] call HMT_REJOUE } forEach _bras;

        terminate _oeil;
        { deleteVehicle _x } forEach HMT_DEF;
        deleteGroup _gD;
        sleep 3;
    } forEach HMT_DATA;

    "HMT|ESC|TERMINE|1" call HMT_LOG;
};
