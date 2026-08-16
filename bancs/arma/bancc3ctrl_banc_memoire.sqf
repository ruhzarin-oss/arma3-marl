// banc_memoire.sqf — UNE FOIS REPÉRÉ, POUR COMBIEN DE TEMPS ?
//
// C'est la question qui dit si le contournement doit être parfait du premier coup. Si la
// connaissance ne s'efface jamais, se faire voir une seule fois est définitif : l'angle mort
// est un capital qu'on dépense une fois. Si elle décroît, il y a un jeu à jouer — se replier,
// attendre, revenir.
//
// CE QUI EST DÉJÀ CERTIFIÉ ⟨03/08, trois bancs, 121 essais⟩
//   cône : 18/18 repérés vers 105 m · hors cône : 0/26
//   couché : invisible au-delà de 130 m, inutile en deçà de 100
//   tirer depuis le dos : révèle mais PLAFONNE à 1,50, jamais 4,00
//
// LE DISPOSITIF. On établit d'abord la connaissance : l'homme est placé dans le cône jusqu'à
// ce que le camp le connaisse pleinement. Puis on le retire de la vue — sans le supprimer —
// et on relève la connaissance toutes les dix secondes pendant cinq minutes.
//
// TROIS CONDITIONS :
//   « efface »  l'homme passe dans le dos des défenseurs (perte de vue par orientation)
//   « reste »   il demeure dans le cône                  -> CONTRÔLE : ne doit PAS décroître
//   « jamais »  il est placé d'emblée dans le dos        -> CONTRÔLE NUL : doit rester à 0
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · si « reste » décroît aussi, ce n'est pas la perte de vue qu'on mesure mais un oubli
//     automatique du moteur, et la comparaison ne vaut rien.
//   · si « jamais » monte au-dessus de 0,5, quelque chose d'autre renseigne les défenseurs.
//   · si la connaissance initiale n'atteint pas 3,0 avant le retrait, l'essai est écarté :
//     on ne mesure pas l'effacement de ce qui n'a jamais été acquis.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|MM|debut|1" call HMT_LOG;

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
                        } forEach [[0,120,0],[0,-120,0],[60,0,0],[-60,0,0],[0,60,0],[0,-60,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [8, 14, 22, 32];
    if (count _base == 0) exitWith { "HMT|MM|ECHEC|terrain" call HMT_LOG };
    (format ["HMT|MM|terrain|%1|%2", round (_base select 0), round (_base select 1)]) call HMT_LOG;

    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        // CONFIGURATION REPRISE À L'IDENTIQUE du banc couvert, dont le contrôle de présence
        // donnait 4,00. Premier jet : j'avais remplacé AUTOCOMBAT par MOVE — modification non
        // testée, et plus rien n'était détecté. On ne change pas ce qui marche sans le remesurer.
        _u setPosATL _p; _u allowDamage false; removeAllWeapons _u;
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "ANIM";
        _u setBehaviour "SAFE"; _u setUnitPos "UP"; _u setDir 0;
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    [] spawn { while { true } do { { _x setDir 0; _x setFormDir 0 } forEach HMT_DEF; sleep 0.5 } };
    sleep 3;
    (format ["HMT|MM|ligne|%1|caps|%2", count HMT_DEF, str (HMT_DEF apply { round (getDir _x) })]) call HMT_LOG;

    HMT_SU = { private _k = 0; { private _v = _x knowsAbout _this; if (_v > _k) then { _k = _v } } forEach HMT_DEF; _k };

    HMT_ESSAI = {
        params ["_cond", "_rep"];
        private _g = createGroup west;
        private _devant = _base vectorAdd [0, 100, 0];      // 100 m : distance à laquelle le banc couvert mesurait 4,00
        private _derriere = _base vectorAdd [0, -100, 0];   // dans leur dos, même distance
        private _dep = if (_cond == "jamais") then { _derriere } else { _devant };
        private _a = _g createUnit ["B_Soldier_F", _dep, [], 0, "NONE"];
        _a setPosATL _dep; _a allowDamage false; removeAllWeapons _a;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a setUnitPos "UP";

        // ---- phase 1 : établir la connaissance (ou son absence) ----
        private _k0 = 0;
        for "_s" from 1 to 24 do { sleep 5; _k0 = _a call HMT_SU };
        (format ["HMT|MM|acquis|%1|%2|%3", _cond, _rep, (round (_k0*100))/100]) call HMT_LOG;

        // un essai qui n'a rien acquis n'a rien à effacer
        if (_cond != "jamais" && _k0 < 3.0) exitWith {
            (format ["HMT|MM|ECARTE|%1|%2|acquis|%3", _cond, _rep, (round (_k0*100))/100]) call HMT_LOG;
            deleteVehicle _a; deleteGroup _g;
        };

        // ---- phase 2 : retrait de la vue (ou non, selon la condition) ----
        if (_cond == "efface") then { _a setPosATL _derriere };

        // ---- phase 3 : suivre la décroissance ----
        for "_s" from 1 to 30 do {
            sleep 10;
            (format ["HMT|MM|suivi|%1|%2|%3|%4", _cond, _rep, _s*10,
                     (round ((_a call HMT_SU)*100))/100]) call HMT_LOG;
        };
        private _kf = _a call HMT_SU;
        (format ["HMT|MM|fin|%1|%2|debut|%3|fin|%4", _cond, _rep,
                 (round (_k0*100))/100, (round (_kf*100))/100]) call HMT_LOG;

        deleteVehicle _a; deleteGroup _g;
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 8;
    };

    // CONTRÔLE DE PRÉSENCE AVANT LE PLAN — neuf essais gâchés la fois précédente faute
    // d'avoir vérifié que l'acquisition se faisait.
    private _gT = createGroup west;
    private _t = _gT createUnit ["B_Soldier_F", (_base vectorAdd [0,100,0]), [], 0, "NONE"];
    _t setPosATL (_base vectorAdd [0,100,0]); _t allowDamage false; removeAllWeapons _t;
    _t disableAI "PATH"; _t disableAI "AUTOCOMBAT"; _t setUnitPos "UP";
    private _kc = 0;
    for "_s" from 1 to 20 do { sleep 5; _kc = _t call HMT_SU };
    (format ["HMT|MM|controle_presence|%1", (round (_kc*100))/100]) call HMT_LOG;
    deleteVehicle _t; deleteGroup _gT;
    { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
    if (_kc < 3.0) exitWith { "HMT|MM|ECHEC|acquisition_impossible" call HMT_LOG };
    "HMT|OK|mm_presence|1" call HMT_LOG;
    sleep 10;

    private _plan = [];
    { private _c = _x; for "_r" from 1 to 3 do { _plan pushBack [_c, _r] } } forEach ["efface", "reste", "jamais"];
    _plan = _plan call BIS_fnc_arrayShuffle;
    (format ["HMT|MM|plan|%1", count _plan]) call HMT_LOG;
    { _x call HMT_ESSAI } forEach _plan;
    "HMT|MM|TERMINE|1" call HMT_LOG;
};
