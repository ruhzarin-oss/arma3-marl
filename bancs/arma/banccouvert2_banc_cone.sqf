// banc_cone.sqf — OÙ EXACTEMENT LE CÔNE SE FERME-T-IL ?
//
// CE QUI EST DÉJÀ CERTIFIÉ ⟨03/08, quatre bancs, 121 essais⟩
//   0° et 45° : repéré 18/18 · 90°, 135°, 180° : 0/26
//   la bascule est donc ENTRE 45° et 90°, jamais localisée.
//   Le simulateur maison utilise 60°, valeur codée sans vérification.
//
// CE BANC la localise au pas de 5°, et à DEUX distances — le cône pourrait s'ouvrir de près
// et se fermer de loin, ou l'inverse. On ne le sait pas.
//
// CONFIGURATION REPRISE À L'IDENTIQUE des bancs qui marchent. ⟨règle payée aujourd'hui : une
// commande de coupure d'IA remplacée sans remesure a rendu un banc entièrement aveugle⟩
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE DE PRÉSENCE : à 0°, la détection DOIT atteindre 4,00. Passé AVANT le plan.
//   · CONTRÔLE NUL : à 180°, la connaissance doit rester à 0.
//   · Si la transition n'est pas monotone — détecté à 70° mais pas à 60° — c'est du bruit
//     et non un seuil ; on ne conclut pas à une largeur.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|CN|debut|1" call HMT_LOG;

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
                        } forEach [[0,200,0],[0,-200,0],[200,0,0],[-200,0,0],
                                   [141,141,0],[-141,141,0],[141,-141,0],[-141,-141,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [8, 14, 22, 32];
    if (count _base == 0) exitWith { "HMT|CN|ECHEC|terrain" call HMT_LOG };
    (format ["HMT|CN|terrain|%1|%2", round (_base select 0), round (_base select 1)]) call HMT_LOG;

    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false; removeAllWeapons _u;
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "ANIM";
        _u setBehaviour "SAFE"; _u setUnitPos "UP"; _u setDir 0;
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    [] spawn { while { true } do { { _x setDir 0; _x setFormDir 0 } forEach HMT_DEF; sleep 0.5 } };
    sleep 3;
    (format ["HMT|CN|ligne|%1|caps|%2", count HMT_DEF, str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

    HMT_SU = { private _k = 0; { private _v = _x knowsAbout _this; if (_v > _k) then { _k = _v } } forEach HMT_DEF; _k };

    HMT_ESSAI = {
        params ["_az", "_dist", "_rep"];
        private _p = _base vectorAdd [_dist * sin _az, _dist * cos _az, 0];
        if (surfaceIsWater _p) exitWith { -1 };
        private _g = createGroup west;
        private _a = _g createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _a setPosATL _p; _a allowDamage false; removeAllWeapons _a;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a setUnitPos "UP"; _a setDir (_az + 180);
        private _k = 0;
        for "_s" from 1 to 12 do { sleep 5; _k = _a call HMT_SU };
        (format ["HMT|CN|essai|%1|%2|%3|know|%4", _az, _dist, _rep, (round (_k*100))/100]) call HMT_LOG;
        deleteVehicle _a; deleteGroup _g;
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 5;
        _k
    };

    // LE TERRAIN EST CHERCHÉ JUSQU'À CE QUE LE CONTRÔLE PASSE.
    // Le tour précédent est tombé sur un endroit où la vue ne portait pas — végétation, sans
    // doute, que la recherche de planéité ne teste pas. Le garde-fou a bien refusé de lancer
    // 24 essais sur un terrain aveugle, mais il ABANDONNAIT au lieu de réessayer.
    // Ici on déplace la ligne défensive et on recommence, jusqu'à cinq terrains.
    private _kp = 0; private _kn = 0; private _ok = false;
    for "_essai" from 1 to 5 do {
        if (!_ok) then {
            _kp = [0, 100, 0] call HMT_ESSAI;
            _kn = [180, 100, 0] call HMT_ESSAI;
            (format ["HMT|CN|controles|terrain|%1|%2|essai|%3|presence|%4|nul|%5",
                     round (_base select 0), round (_base select 1), _essai,
                     (round (_kp*100))/100, (round (_kn*100))/100]) call HMT_LOG;
            if (_kp >= 3.0 && _kn <= 0.5) then { _ok = true }
            else {
                // on déplace toute la ligne ailleurs et on recommence
                private _n = [];
                for "_t" from 0 to 3000 do {
                    if (count _n == 0) then {
                        private _c = [1200 + random 4200, 4200 + random 3000, 0];
                        private _h = getTerrainHeightASL _c;
                        if (!(surfaceIsWater _c) && _h > 2) then {
                            private _bon = true;
                            { private _q = _c vectorAdd _x;
                              if (surfaceIsWater _q) then { _bon = false };
                              if (abs ((getTerrainHeightASL _q) - _h) > 14) then { _bon = false };
                              // on exige aussi qu il n y ait AUCUN objet de terrain a proximite :
                              // c est ce qui manquait, et c est ce qui rendait la vue aveugle
                              if (count (nearestTerrainObjects [_q, ["TREE","SMALL TREE","BUSH"], 40]) > 0) then { _bon = false };
                            } forEach [[0,0,0],[0,50,0],[0,100,0],[0,-100,0],[40,50,0],[-40,50,0]];
                            if (_bon) then { _n = _c };
                        };
                    };
                };
                if (count _n > 0) then {
                    _base = _n;
                    { _x setPosATL (_base vectorAdd [(HMT_DEF find _x) * 16 - 40, 0, 0]) } forEach HMT_DEF;
                    sleep 3;
                };
            };
        };
    };
    if (!_ok) exitWith { "HMT|CN|ECHEC|aucun_terrain_ou_la_vue_porte" call HMT_LOG };
    (format ["HMT|OK|cn_controles|1|terrain|%1|%2", round (_base select 0), round (_base select 1)]) call HMT_LOG;

    private _plan = [];
    { private _d = _x;
      { private _az = _x;
        for "_r" from 1 to 3 do { _plan pushBack [_az, _d, _r] };
      // RESSERREMENT AU BON ENDROIT. Le tour précédent a établi : plateau plat à 4,00 de 0°
      // à 30°, zéro dès 40°. J'avais resserré autour de 47° — cinq azimuts pour rien, tous
      // à zéro. La bascule est entre 30 et 40, et c'est là qu'il faut des points.
      // On garde 30 et 40 comme ancres connues, et on découpe l'intervalle au degré près.
      // 60° est rejoué quatre fois : il avait donné 0,86 puis 0,00, seule valeur incohérente
      // du tour précédent. Deux essais ne tranchent pas entre bruit et effet.
      } forEach [30, 32, 34, 36, 38, 40, 60, 60];
    } forEach [100];      // une seule distance : la grille s'est élargie, le temps est borné
    _plan = _plan call BIS_fnc_arrayShuffle;
    (format ["HMT|CN|plan|%1", count _plan]) call HMT_LOG;
    { _x call HMT_ESSAI } forEach _plan;
    "HMT|CN|TERMINE|1" call HMT_LOG;
};
