// banc_couvert.sqf — LE COUVERT CHANGE-T-IL LA DONNE ?
//
// CE QUI EST DÉJÀ CERTIFIÉ ⟨banc du 03/08, 44 essais⟩
//   dans le cône : repéré 18 fois sur 18, vers 105 m
//   hors du cône : jamais, 0 sur 26
//   la posture en terrain NU : 9 m de gain sur 108, négligeable
//
// LA QUESTION LAISSÉE OUVERTE. Le banc précédent était en terrain découvert. Se coucher n'y
// vaut rien. Mais DERRIÈRE un muret ? Si le couvert transforme la posture en vraie décision,
// l'agent retrouve un répertoire et tout le chantier « répertoire ouvert » redevient légitime.
// Sinon, on saura définitivement que seule la direction compte.
//
// LE DISPOSITIF, différent du précédent. Plus d'approche mobile : l'approchant est POSÉ à une
// distance fixe, derrière un couvert donné, dans une posture donnée. On attend, et on relève
// ce que le camp finit par savoir de lui. Ça isole l'effet couvert x posture sans le mélanger
// à la dynamique de l'approche.
//
// TROIS COUVERTS : rien · un obstacle bas (~1 m) · un mur (~1,8 m)
// TROIS POSTURES : debout · accroupi · couché
// TROIS DISTANCES : 60 m · 100 m · 150 m
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE DE PRÉSENCE : terrain nu, debout, 60 m -> DOIT être repéré. Sinon rien ne vaut.
//   · CONTRÔLE DU DÉCOR : chaque couvert est VÉRIFIÉ en travers de la ligne de vue avant
//     l'essai. ⟨le 02/08, six essais ont été perdus parce que le mur était posé le long de la
//     ligne au lieu d'être en travers, et je le croyais sur parole⟩
//   · CONTRÔLE NUL : la même condition rejouée doit donner des résultats voisins.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|CV|debut|1" call HMT_LOG;

[] spawn {
    sleep 20;

    // ---------- un terrain plat, cherché et non supposé ----------
    private _base = []; private _tol = 0;
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 2500 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        {
                            private _q = _c vectorAdd _x;
                            if (surfaceIsWater _q) then { _ok = false };
                            if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                        } forEach [[0,60,0],[0,100,0],[0,150,0],[0,180,0],[40,100,0],[-40,100,0],
                                   [60,0,0],[-60,0,0],[0,-40,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [8, 14, 20, 30];
    if (count _base == 0) exitWith { "HMT|CV|ECHEC|aucun_terrain_plat" call HMT_LOG };
    (format ["HMT|CV|terrain|%1|%2|denivele|%3", round (_base select 0), round (_base select 1), _tol]) call HMT_LOG;

    // ---------- la ligne défensive, cap verrouillé ⟨sans quoi le résultat s'inverse⟩ ----------
    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p;
        removeAllWeapons _u; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "ANIM";
        _u setBehaviour "SAFE"; _u setUnitPos "UP"; _u setDir 0;
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    [] spawn { while { true } do { { _x setDir 0; _x setFormDir 0 } forEach HMT_DEF; sleep 0.5 } };
    sleep 3;
    (format ["HMT|CV|ligne|%1|caps|%2", count HMT_DEF, str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

    // ---------- un essai ----------
    HMT_ESSAI = {
        params ["_couvert", "_posture", "_dist", "_rep"];
        private _p = _base vectorAdd [0, _dist, 0];      // plein NORD : dans leur cône
        private _g = createGroup west;
        private _a = _g createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _a setPosATL _p;
        removeAllWeapons _a; _a allowDamage false;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT";
        _a setUnitPos _posture; _a setDir 180;

        // ---------- LE COUVERT, posé JUSTE devant lui, côté défenseurs ----------
        private _obs = [];
        if (_couvert != "aucun") then {
            private _cls = if (_couvert == "bas") then { "Land_CncBarrier_F" } else { "Land_CncWall4_F" };
            // ON ESSAIE LES DEUX ORIENTATIONS ET ON GARDE CELLE QUI BLOQUE VRAIMENT.
            // ⟨le 02/08 j'avais mesuré que dir 0 met ce mur en travers d'une ligne nord-sud,
            //  et dir 90 le range LE LONG. Six essais perdus ce jour-là. Ici on ne suppose pas :
            //  on pose, on mesure, on garde.⟩
            private _meilleur = -1; private _score = -1;
            {
                private _d = _x; private _tmp = [];
                {
                    private _o = createVehicle [_cls, [0,0,0], [], 0, "CAN_COLLIDE"];
                    _o setDir _d;
                    _o setPosATL (_p vectorAdd [_x, -3, 0]);
                    _tmp pushBack _o;
                } forEach [-9, -6, -3, 0, 3, 6, 9];
                sleep 1;
                private _n = 0;
                {
                    private _i = lineIntersectsSurfaces [eyePos _x, aimPos _a, _x, _a, true, 4, "VIEW", "FIRE"];
                    if (count _i > 0) then { _n = _n + 1 };
                } forEach HMT_DEF;
                if (_n > _score) then { _score = _n; _meilleur = _d };
                { deleteVehicle _x } forEach _tmp;
                sleep 0.5;
            } forEach [0, 90];
            {
                private _o = createVehicle [_cls, [0,0,0], [], 0, "CAN_COLLIDE"];
                _o setDir _meilleur;
                _o setPosATL (_p vectorAdd [_x, -3, 0]);
                _obs pushBack _o;
            } forEach [-9, -6, -3, 0, 3, 6, 9];
            (format ["HMT|CV|decor|%1|dir_retenue|%2|bloque_a_lessai|%3", _couvert, _meilleur, _score]) call HMT_LOG;
        };
        sleep 2;

        // CONTRÔLE DU DÉCOR : le couvert intercepte-t-il RÉELLEMENT la ligne de vue ?
        private _bloque = 0;
        {
            private _i = lineIntersectsSurfaces [eyePos _x, aimPos _a, _x, _a, true, 4, "VIEW", "FIRE"];
            if (count _i > 0) then { _bloque = _bloque + 1 };
        } forEach HMT_DEF;
        private _hauteur = if (count _obs > 0) then { ((boundingBoxReal (_obs select 0)) select 1) select 2 } else { 0 };

        // ---------- on laisse le moteur percevoir ----------
        private _kmax = 0;
        for "_s" from 1 to 30 do {
            sleep 1;
            { private _v = _x knowsAbout _a; if (_v > _kmax) then { _kmax = _v } } forEach HMT_DEF;
        };

        (format ["HMT|CV|essai|%1|%2|%3|%4|know|%5|bloque|%6|sur|%7|hauteur|%8",
                 _couvert, _posture, _dist, _rep, (round (_kmax*100))/100,
                 _bloque, count HMT_DEF, (round (_hauteur*100))/100]) call HMT_LOG;

        { deleteVehicle _x } forEach _obs;
        deleteVehicle _a; deleteGroup _g;
        // on efface la mémoire du camp entre deux essais ⟨knowsAbout est de CAMP⟩
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 4;
        _kmax
    };

    // ---------- CONTRÔLE DE PRÉSENCE ----------
    private _k = ["aucun", "UP", 60, 0] call HMT_ESSAI;
    (format ["HMT|CV|controle_presence|know|%1", (round (_k*100))/100]) call HMT_LOG;
    if (_k < 1.0) exitWith { "HMT|CV|ECHEC|controle_presence" call HMT_LOG };
    "HMT|OK|cv_presence|1" call HMT_LOG;

    // ---------- LE PLAN ----------
    private _plan = [];
    {
        private _c = _x;
        { private _po = _x;
          { private _d = _x;
            for "_r" from 1 to 2 do { _plan pushBack [_c, _po, _d, _r] };
          } forEach [60, 100, 150];
        } forEach ["UP", "MIDDLE", "DOWN"];
    } forEach ["aucun", "bas", "haut"];
    _plan = _plan call BIS_fnc_arrayShuffle;
    (format ["HMT|CV|plan|%1|essais", count _plan]) call HMT_LOG;

    { _x call HMT_ESSAI } forEach _plan;
    "HMT|CV|TERMINE|1" call HMT_LOG;
};
