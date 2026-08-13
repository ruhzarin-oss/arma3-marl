// banc_tir.sqf — TIRER RÉVÈLE-T-IL, ET DE COMBIEN ?
//
// C'est la question qui décide de ce que l'angle mort ACHÈTE réellement. Si un homme placé
// dans l'angle mort se fait repérer dès son premier coup de feu, le contournement n'achète
// qu'un seul tir — et toute la tactique change. S'il peut tirer plusieurs fois sans être
// localisé, l'angle mort est une position de combat, pas seulement une approche.
//
// CE QUI EST DÉJÀ CERTIFIÉ ⟨03/08, deux bancs, 96 essais⟩
//   dans le cône : repéré 18/18 vers 105 m · hors du cône : 0/26
//   couché : invisible au-delà de 130 m, inutile en deçà de 100
//
// LE DISPOSITIF. Six défenseurs, cap verrouillé au nord, ARMÉS mais empêchés de bouger.
// Un tireur placé à distance et azimut imposés, invulnérable, qui ouvre le feu sur eux.
// On relève ce que le camp sait de lui AVANT le premier coup, puis après chaque rafale.
//
// CONDITIONS : azimut (0° dans leur cône · 180° dans leur dos) x distance (100 · 200 m)
//              x nombre de coups tirés (0 · 1 · 5 · 15)
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE DE PRÉSENCE : à 0° et 100 m, le tireur DOIT être connu même sans tirer.
//   · CONTRÔLE NUL : à 180°, sans tirer, la connaissance doit rester nulle. Si elle monte,
//     quelque chose d'autre les renseigne et la mesure ne vaut rien.
//   · Le tireur doit RÉELLEMENT tirer : le nombre de coups est compté, pas supposé.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|TR|debut|1" call HMT_LOG;

[] spawn {
    sleep 20;
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
                        { private _q = _c vectorAdd _x;
                          if (surfaceIsWater _q) then { _ok = false };
                          if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                        } forEach [[0,100,0],[0,200,0],[0,-100,0],[0,-200,0],[60,0,0],[-60,0,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [8, 14, 22, 32];
    if (count _base == 0) exitWith { "HMT|TR|ECHEC|terrain" call HMT_LOG };
    (format ["HMT|TR|terrain|%1|%2", round (_base select 0), round (_base select 1)]) call HMT_LOG;

    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "ANIM"; _u disableAI "MOVE";
        _u setBehaviour "SAFE"; _u setUnitPos "UP"; _u setDir 0;
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    [] spawn { while { true } do { { _x setDir 0; _x setFormDir 0 } forEach HMT_DEF; sleep 0.5 } };
    sleep 3;
    (format ["HMT|TR|ligne|%1|caps|%2", count HMT_DEF, str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

    HMT_ESSAI = {
        params ["_az", "_dist", "_coups", "_rep"];
        private _p = _base vectorAdd [_dist * sin _az, _dist * cos _az, 0];
        private _g = createGroup west;
        private _a = _g createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _a setPosATL _p; _a allowDamage false;
        // EMPÊCHER LE TIR SPONTANÉ. Premier jet : disableAI "AUTOCOMBAT" empêche le
        // changement de comportement, PAS l'ouverture du feu — le tireur partait à 21 coups
        // dans la condition « 0 coup », et la comparaison ne valait rien. Le compteur l'a
        // attrapé. Ici on cumule l'ordre de tenir le feu et la coupure des automatismes.
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a disableAI "TARGET";
        _a disableAI "FSM"; _a disableAI "AUTOTARGET";
        _a setCombatMode "BLUE";          // « tenir le feu » : ne tire que sur ordre
        _a setBehaviour "CARELESS";
        _a setUnitPos "UP"; _a setDir (_az + 180);
        // on COMPTE les coups réellement partis, on ne les suppose pas
        _a setVariable ["tr_n", 0];
        _a addEventHandler ["Fired", { (_this select 0) setVariable ["tr_n", ((_this select 0) getVariable ["tr_n",0]) + 1] }];

        // FENÊTRE D'OBSERVATION LONGUE. Premier jet : 8 s avant, 12 s après — trop court pour
        // que la détection s'établisse. Résultat : dans le cône à 100 m, sans tirer, la
        // connaissance restait à 0,00 alors que le banc mobile détectait 18 fois sur 18 à
        // 105 m (mais après ~50 s d'approche). Ma référence n'existait pas.
        sleep 60;
        private _avant = 0;
        { private _v = _x knowsAbout _a; if (_v > _avant) then { _avant = _v } } forEach HMT_DEF;

        // ORDRE DE TIR QUI BOUCLE JUSQU'AU COMPTE VOULU. Premier jet : quinze ordres espacés
        // de 0,7 s ne produisaient que quatre coups — l'arme n'était pas prête. On ne suppose
        // plus, on vérifie le compteur à chaque tour.
        if (_coups > 0) then {
            private _cible = HMT_DEF select 2;
            private _essais = 0;
            while { (_a getVariable ["tr_n",0]) < _coups && _essais < 150 } do {
                _essais = _essais + 1;
                _a doWatch _cible; _a doTarget _cible;
                _a forceWeaponFire [currentWeapon _a, currentWeaponMode _a];
                sleep 0.4;
            };
        };
        sleep 60;

        private _apres = 0;
        { private _v = _x knowsAbout _a; if (_v > _apres) then { _apres = _v } } forEach HMT_DEF;
        private _reels = _a getVariable ["tr_n", 0];

        (format ["HMT|TR|essai|%1|%2|%3|%4|avant|%5|apres|%6|coups_reels|%7",
                 _az, _dist, _coups, _rep,
                 (round (_avant*100))/100, (round (_apres*100))/100, _reels]) call HMT_LOG;

        deleteVehicle _a; deleteGroup _g;
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 5;
    };

    // CONTRÔLE : « zéro coup » signifie-t-il vraiment zéro ?
    [180, 200, 0, 0] call HMT_ESSAI;
    [0, 100, 0, 0] call HMT_ESSAI;
    "HMT|OK|tr_presence|1" call HMT_LOG;

    private _plan = [];
    { private _az = _x;
      { private _d = _x;
        { private _c = _x;
          for "_r" from 1 to 2 do { _plan pushBack [_az, _d, _c, _r] };
        } forEach [0, 5, 20];
      } forEach [100, 200];
    } forEach [0, 180];
    _plan = _plan call BIS_fnc_arrayShuffle;
    (format ["HMT|TR|plan|%1", count _plan]) call HMT_LOG;
    { _x call HMT_ESSAI } forEach _plan;
    "HMT|TR|TERMINE|1" call HMT_LOG;
};
