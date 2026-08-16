// banc150.sqf — LE BANC REFAIT A 150 M.
//
// POURQUOI IL EST REFAIT. Le banc precedent faisait partir l'approchant a 80 m, alors que la
// detection frontale est mesuree a 105 m dans Arma ⟨banc du cone, 03/08, 18/18⟩ : il partait
// DEJA VU. Mesure du 04/08 sur les 40 trajectoires rejouees : 24 des 34 reperees l'etaient
// dans les 12 premiers metres, ecart interquartile 8 m sur 40 m utiles — 20 % de dynamique.
// L'instrument etait ecrase contre son plafond. Il refusait tout le monde sans rien mesurer,
// y compris le chemin PARFAIT.
//
// CE QU'ON TESTE ICI : l'INSTRUMENT, pas l'agent. A 150 m, la distance de reperage sait-elle
// separer des trajectoires ? Tant que la reponse est non, aucune certification ne vaut.
//
// QUATRE BRAS sur chaque configuration, tous de 150 m a 40 m du centre :
//   droite        le temoin
//   oracle        le meilleur chemin DEPUIS CE DEPART   ⟨plus court chemin de goulot sur le
//                 damier d'ombre — la geometrie promet qu'il achete 24 % du pic⟩
//   oracle_libre  le meilleur chemin en CHOISISSANT son point de depart sur le cercle
//   droite_bis    la droite rejouee -> CONTROLE NUL
//
// CE QUI FERAIT ECHOUER LA MESURE — ecrit avant :
//   P1 PRESENCE  : la ligne droite DOIT etre reperee. Sinon la position ne voit rien.
//   P2 DYNAMIQUE : l'ecart interquartile des distances doit couvrir >= 27 m des 110 m utiles.
//                  C'EST LE CONTROLE QUI MANQUAIT.
//   P3 NUL       : droite et droite_bis doivent se rejoindre a moins de 15 m.
//   P4 REUSSITE  : oracle_libre doit etre repere >= 25 % plus loin que la droite. Sinon
//                  aucun agent ne peut passer, et c'est la TACHE qu'il faut changer.
//
// LES POSITIONS DES DEFENSEURS SONT MESUREES, PAS SUPPOSEES. 13 configurations sur 20 ont des
// defenseurs a moins d'un metre les uns des autres, cinq strictement confondus. Arma les
// repoussera. On journalise donc ce qu'il en fait REELLEMENT, au lieu de le decouvrir dans
// les resultats. ⟨le 03/08, un cap suppose et non mesure avait INVERSE une conclusion⟩

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
call compile preprocessFileLineNumbers "donnees_banc150.sqf";
if (isNil "HMT_DATA") exitWith { "HMT|B150|ECHEC|donnees_non_chargees" call HMT_LOG };
if (!(HMT_DATA isEqualType [])) exitWith { "HMT|B150|ECHEC|donnees_mal_formees" call HMT_LOG };
(format ["HMT|B150|debut|%1|configs", count HMT_DATA]) call HMT_LOG;

[] spawn {
    sleep 20;

    // ---------- un cercle de 155 m plat et degage, CHERCHE et non impose ----------
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
    if (count _base == 0) exitWith { "HMT|B150|ECHEC|aucun_terrain" call HMT_LOG };
    (format ["HMT|B150|terrain|%1|%2|denivele|%3", round (_base select 0),
             round (_base select 1), _tol]) call HMT_LOG;

    HMT_SU = { private _k = 0; { private _v = _x knowsAbout _this; if (_v > _k) then { _k = _v } } forEach HMT_DEF; _k };

    // ---------- rejouer une trajectoire ----------
    HMT_REJOUE = {
        params ["_pts", "_lib", "_cfg"];
        private _g = createGroup west;
        private _p0 = _base vectorAdd [(_pts select 0) select 0, (_pts select 0) select 1, 0];
        private _a = _g createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
        _a setPosATL _p0; _a allowDamage false; removeAllWeapons _a;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a setUnitPos "UP";
        sleep 2;
        private _k = 0; private _dDetect = -1; private _capMin = 999;
        {
            private _p = _base vectorAdd [_x select 0, _x select 1, 0];
            _a setPosATL _p;
            sleep 1.2;
            private _v = _a call HMT_SU;
            if (_v > _k) then { _k = _v };
            if (_v >= 1.5 && _dDetect < 0) then {
                _dDetect = round (sqrt (((_x select 0)^2) + ((_x select 1)^2)));
            };
        } forEach _pts;
        private _fin = (_pts select ((count _pts) - 1));
        private _reste = round (sqrt (((_fin select 0)^2) + ((_fin select 1)^2)));
        (format ["HMT|B150|essai|%1|%2|know|%3|reste|%4|dist_detect|%5|points|%6", _cfg, _lib,
                 (round (_k*100))/100, _reste, _dDetect, count _pts]) call HMT_LOG;
        deleteVehicle _a; deleteGroup _g;
        // on efface la memoire du camp entre deux bras ⟨knowsAbout est de CAMP et NE DECROIT PAS⟩
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
        sleep 4;

        // CE QU'ARMA A REELLEMENT FAIT DES DEFENSEURS — mesure, pas suppose
        private _derive = 0;
        {
            private _v = _x getVariable ["voulu", [0,0]];
            private _r = _base vectorFromTo (getPosATL _x);
            private _reel = [(getPosATL _x select 0) - (_base select 0),
                             (getPosATL _x select 1) - (_base select 1)];
            private _e = sqrt ((((_reel select 0)-(_v select 0))^2) + (((_reel select 1)-(_v select 1))^2));
            if (_e > _derive) then { _derive = _e };
        } forEach HMT_DEF;
        (format ["HMT|B150|config|%1|defenseurs|%2|derive_max|%3|caps|%4", _n, count HMT_DEF,
                 (round (_derive*10))/10, str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

        { [_x select 1, _x select 0, _n] call HMT_REJOUE } forEach _bras;

        terminate _garde;
        { deleteVehicle _x } forEach HMT_DEF;
        deleteGroup _gD;
        sleep 3;
    } forEach HMT_DATA;

    "HMT|B150|TERMINE|1" call HMT_LOG;
};
