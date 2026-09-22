// =====================================================================
// CHACAL MULTI - K cellules de la phase 2 dans un seul serveur ( avis de Fable du 22/09, depot/multi/ ).
//
// Chaque cellule est le banc seul tout entier, renomme ( c<k>\ ) : son monde, sa garnison, son Oracle, son
// detachement, son enregistreur, son verdict. Ce fichier ne fait que quatre choses :
//   1. monter les cellules une par une, dans l'ordre du banc seul ;
//   2. les faire partir ENSEMBLE ( MULTI_DEPART ), une fois toutes les emprises connues ;
//   3. mesurer ce que l'episode multiple peut abimer : la CHARGE ( images par seconde ), la PERCEPTION
//      ( sonde de connaissance hors cellules ) et l'INDEPENDANCE ( connaissance croisee entre cellules ) ;
//   4. fermer : toute cellule non finie a MULTI_TMAX est CENSUREE, jamais comptee comme une issue.
// =====================================================================
call compile preprocessFileLineNumbers "multi\commun.sqf";
MULTI_K = ["MULTI_K", 1] call BIS_fnc_getParamValue;
MULTI_TMAX = ["MULTI_TMAX", 1200] call BIS_fnc_getParamValue;
MULTI_SONDE = ["MULTI_SONDE", 1] call BIS_fnc_getParamValue;
MULTI_ESPACEMENT = ["MULTI_ESPACEMENT", 3000] call BIS_fnc_getParamValue;
MULTI_FINI = false;
(format ["OK|debut|%1|version|%2|k|%3|tmax|%4|sonde|%5|espacement|%6|moteur|%7",
    round (diag_tickTime * 100) / 100, MULTI_VERSION, MULTI_K, MULTI_TMAX, MULTI_SONDE, MULTI_ESPACEMENT, productVersion select 2]) call MULTI_LOG;

// --- 1. monter ---
MULTI_VIVANTES = [];
for "_k" from 1 to MULTI_K do {
    private _t0 = diag_tickTime;
    private _ok = [_k] call MULTI_fnc_monter;
    if (_ok) then { MULTI_VIVANTES pushBack _k; [_k] call MULTI_fnc_enregistrerEmprise };
    (format ["OK|cellule|%1|montee|%2|duree_reelle|%3|unites_total|%4|groupes_total|%5", _k, (if (_ok) then {1} else {0}),
        round ((diag_tickTime - _t0) * 10) / 10, count allUnits, count allGroups]) call MULTI_LOG;
};

// l'espacement REEL, mesure sur les mondes tires ( et non sur la table du lanceur )
{
    private _a = _x;
    {
        private _b = _x;
        if ((_a select 0) < (_b select 0)) then {
            (format ["E|espacement|%1|%2|metres|%3", _a select 0, _b select 0, round ([_a select 1, _b select 1] call MULTI_fnc_ecartMin)]) call MULTI_LOG;
        };
    } forEach MULTI_EMPRISES;
} forEach MULTI_EMPRISES;

// --- 3a. la charge : un compteur d'images dans le contexte NON ORDONNANCE, immunise contre la famine du scheduler ---
MULTI_IMAGES = 0; MULTI_T_IMAGES = time; MULTI_TR_IMAGES = diag_tickTime;
MULTI_SONDE_ACTIVE = []; // [observateur, cible, t0, cycle, distance]
MULTI_EH_IMAGE = addMissionEventHandler ["EachFrame", {
    MULTI_IMAGES = MULTI_IMAGES + 1;
    // la sonde se lit a chaque image : son delai ne depend pas de l'ordonnanceur
    if (count MULTI_SONDE_ACTIVE > 0) then {
        MULTI_SONDE_ACTIVE params ["_o", "_c", "_t0", "_n", "_d"];
        if (alive _o && { alive _c } && { (_o targetKnowledge _c) select 0 }) then {
            (format ["E|sonde|%1|cycle|%2|connue|1|delai|%3|distance|%4|fps|%5", round (time * 100) / 100, _n,
                round ((time - _t0) * 100) / 100, _d, round diag_fps]) call MULTI_LOG;
            MULTI_SONDE_ACTIVE = [];
        };
    };
    private _dt = diag_tickTime - MULTI_TR_IMAGES;
    if (_dt >= 2) then {
        private _actives = { !(missionNamespace getVariable [format ["MC%1_FIN", _x], true]) } count MULTI_VIVANTES;
        (format ["C|fps|%1|images|%2|reel_s|%3|fps_moteur|%4|fps_min|%5|unites|%6|groupes|%7|scripts|%8|cellules_actives|%9|jeu_s|%10",
            round (time * 100) / 100, MULTI_IMAGES, round (_dt * 100) / 100, round (diag_fps * 10) / 10, round (diag_fpsMin * 10) / 10,
            count allUnits, count allGroups, str diag_activeScripts, _actives, round ((time - MULTI_T_IMAGES) * 100) / 100]) call MULTI_LOG;
        MULTI_IMAGES = 0; MULTI_TR_IMAGES = diag_tickTime; MULTI_T_IMAGES = time;
    };
}];

// --- les lieux de la sonde, choisis AVANT le depart : loin de toutes les emprises, sans maison, vue franche a 150 m ---
MULTI_SONDE_SITES = [];
if (MULTI_SONDE == 1) then {
    private _essais = 0;
    while { (count MULTI_SONDE_SITES < 12) && { _essais < 3000 } } do {
        _essais = _essais + 1;
        private _c = [3000 + random 24000, 3000 + random 24000, 0];
        if (!surfaceIsWater _c && { count (nearestObjects [_c, ["House"], 60]) == 0 } && { [_c, 0] call MULTI_fnc_loin }) then {
            private _oe = AGLToASL [_c select 0, _c select 1, 1.7];
            private _az = random 360;
            {
                private _t = _c getPos [150, _az + _x];
                if (!surfaceIsWater _t) then {
                    if (([objNull, "VIEW", objNull] checkVisibility [_oe, AGLToASL [_t select 0, _t select 1, 1.6]]) >= 0.9) exitWith { MULTI_SONDE_SITES pushBack [_c, _t] };
                };
            } forEach [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
        };
    };
    (format ["OK|sonde_sites|%1|essais|%2", count MULTI_SONDE_SITES, _essais]) call MULTI_LOG;
};

// --- 2. partir ensemble ---
MULTI_T0 = time;
MULTI_DEPART = true;
(format ["OK|depart|%1|cellules|%2|unites|%3|groupes|%4", round (time * 100) / 100, MULTI_VIVANTES, count allUnits, count allGroups]) call MULTI_LOG;

// --- 3b. l'independance : ce que chaque chef de groupe CONNAIT d'une autre cellule, un tour toutes les 2 s ---
// nearTargets rend la connaissance du groupe du chef, amis compris. Une entree dont la cellule differe de celle du
// chef est un CROISEMENT : ennemi ( fuite a tolerance zero ) ou ami ( proximite, a lire ). La sonde porte deux
// cellules a elle, 100 ( l'observateur ) et 101 ( la cible ) : chaque fois qu'elle est connue, ce journal DOIT la
// voir. C'est son controle positif.
// ! NON ORDONNANCE ET AMORTI ( balayage C3 v1 : l'ordonnanceur est le goulot ) : quatre groupes par image, le tour
// complet en moins d'une seconde a K = 5, sans rien prendre au budget de la logique de mission.
MULTI_CR_G = []; MULTI_CR_I = -1; MULTI_CR_T = time; MULTI_CR_A = [0, [], [], 0, []];
MULTI_EH_CROISE = addMissionEventHandler ["EachFrame", {
    if (MULTI_FINI) exitWith {};
    if (MULTI_CR_I < 0) exitWith {
        if ((time - MULTI_CR_T) >= 2) then { MULTI_CR_G = +allGroups; MULTI_CR_I = 0; MULTI_CR_T = time; MULTI_CR_A = [0, [], [], 0, []] };
    };
    private _fin = (MULTI_CR_I + 4) min (count MULTI_CR_G);
    for "_i" from MULTI_CR_I to (_fin - 1) do {
        private _l = leader (MULTI_CR_G select _i);
        if (!isNull _l && { alive _l }) then {
            private _c = _l getVariable ["multi_c", -1];
            if (_c < 0) then { _c = _l call MULTI_fnc_cellule };
            if (_c >= 1) then {
                MULTI_CR_A set [0, (MULTI_CR_A select 0) + 1];
                private _sl = side (group _l);
                {
                    private _o = _x select 4;
                    if (!isNull _o) then {
                        private _co = _o getVariable ["multi_c", -1];
                        if (_co < 0) then { _co = _o call MULTI_fnc_cellule };
                        if (_co >= 1 && { _co != _c }) then {
                            private _e = [_c, _co, round (_l distance2D _o)];
                            if ((_c >= 100) || { _co >= 100 }) then {
                                if ((_c == 100) && { _co == 101 }) then { MULTI_CR_A set [3, (MULTI_CR_A select 3) + 1] } else {
                                    if ((_c < 100) || { _co < 100 }) then { (MULTI_CR_A select 4) pushBack _e };
                                };
                            } else {
                                if ((_x select 2) != _sl) then { (MULTI_CR_A select 1) pushBack _e } else { (MULTI_CR_A select 2) pushBack _e };
                            };
                        };
                    };
                } forEach (_l nearTargets 30000);
            };
        };
    };
    MULTI_CR_I = _fin;
    if (MULTI_CR_I >= (count MULTI_CR_G)) then {
        MULTI_CR_A params ["_chefs", "_ennemis", "_amis", "_ctrl", "_sonde"];
        (format ["E|croise|%1|chefs|%2|ennemis|%3|amis|%4|controle_sonde|%5|detail_ennemis|%6|detail_amis|%7|sonde_croisee|%8|tour_s|%9",
            round (MULTI_CR_T * 100) / 100, _chefs, count _ennemis, count _amis, _ctrl, str (_ennemis select [0, 6]),
            str (_amis select [0, 6]), count _sonde, round ((time - MULTI_CR_T) * 100) / 100]) call MULTI_LOG;
        MULTI_CR_I = -1;
    };
}];

// --- 3c. la sonde de connaissance : debout, 150 m, nuit, regard pose - la mesure du banc de seuil du 18/09 ---
// Hors de toute cellule. Les lieux sont choisis AVANT le depart ( MULTI_SONDE_SITES ) : la recherche ne pese plus sur
// l'ordonnanceur pendant l'episode. Un cycle par minute environ.
// ! LA SONDE EST LE BANC DE SEUIL DU 18/09, PAS UN HOMME SEUL ( fumee v1 : un observateur seul, qui pivotait par
// doWatch, n'a rien connu en 45 s ). Dix hommes du detachement, TOURNES vers la cible avant de la regarder ( doWatch
// seul pivote en jusqu'a 90 s, patch 2786e65 ) ; le chef de la cible est pose AU point teste, et la visibilite REELLE est
// mesuree ( < 0,3 : cycle refuse, compte a part ).
if ((MULTI_SONDE == 1) && { count MULTI_SONDE_SITES > 0 }) then {
    [] spawn {
        private _n = 0;
        sleep 10;
        while { !MULTI_FINI } do {
            _n = _n + 1;
            (MULTI_SONDE_SITES select ((_n - 1) % (count MULTI_SONDE_SITES))) params ["_p", "_q"];
            private _go = [west, 100] call MULTI_fnc_groupe;
            private _obs = [];
            {
                private _u = _go createUnit [_x, _p getPos [3, _forEachIndex * 36], [], 0, "CAN_COLLIDE"];
                _u setSkill ["spotDistance", 0.75]; _u setSkill ["spotTime", 0.8];
                if ((hmd _u) == "") then { _u linkItem "NVGoggles" };
                _u allowDamage false; doStop _u; _obs pushBack _u;
            } forEach ["B_recon_TL_F", "B_recon_M_F", "B_recon_M_F", "B_recon_exp_F", "B_recon_exp_F", "B_recon_medic_F", "B_recon_LAT_F", "B_recon_F", "B_recon_F", "B_recon_TL_F"];
            _go selectLeader (_obs select 0);
            _go setBehaviour "STEALTH"; _go setCombatMode "GREEN";
            sleep 5;
            private _gc = [east, 101] call MULTI_fnc_groupe;
            {
                private _u = _gc createUnit [_x, (if (_forEachIndex == 0) then { _q } else { _q getPos [2, _forEachIndex * 120] }), [], 0, "CAN_COLLIDE"];
                _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE"; _u setUnitPos "UP"; _u allowDamage false;
            } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
            _gc setCombatMode "BLUE"; _gc setBehaviour "SAFE";
            private _cible = leader _gc;
            sleep 1;
            private _vis = 0;
            // ! l observateur est IGNORE par le rayon : sa propre tete le bouchait ( 5 cycles sur 5 refuses, 22/09 13 h 55 )
            { _vis = _vis max ([_x, "VIEW", _cible] checkVisibility [eyePos _x, eyePos _cible]) } forEach _obs;
            { _x setDir (_x getDir _cible); _x doWatch _cible } forEach _obs;
            private _d = round ((_obs select 0) distance2D _cible);
            private _t0 = time;
            if (_vis < 0.3) then {
                (format ["E|sonde|%1|cycle|%2|connue|-1|delai|-1|distance|%3|visibilite|%4|refus|CIBLE_MASQUEE", round (time * 100) / 100, _n, _d, round (_vis * 100) / 100]) call MULTI_LOG;
            } else {
                MULTI_SONDE_ACTIVE = [leader _go, _cible, time, _n, _d];
                waitUntil { sleep 1; (count MULTI_SONDE_ACTIVE == 0) || { (time - _t0) > 60 } || MULTI_FINI };
                if (count MULTI_SONDE_ACTIVE > 0) then {
                    MULTI_SONDE_ACTIVE = [];
                    (format ["E|sonde|%1|cycle|%2|connue|0|delai|-1|distance|%3|visibilite|%4|fps|%5", round (time * 100) / 100, _n, _d, round (_vis * 100) / 100, round diag_fps]) call MULTI_LOG;
                };
                sleep 4;   // le journal croise doit avoir le temps de voir la connaissance
            };
            { deleteVehicle _x } forEach (units _go + units _gc);
            deleteGroup _go; deleteGroup _gc;
            sleep 10;
        };
    };
};

// --- 4. fermer ---
[] spawn {
    private _faites = [];
    waitUntil {
        sleep 2;
        {
            if (!(_x in _faites) && { missionNamespace getVariable [format ["MC%1_FIN", _x], false] }) then {
                _faites pushBack _x;
                (format ["E|cellule_finie|%1|cellule|%2|depuis_depart|%3", round (time * 100) / 100, _x, round (time - MULTI_T0)]) call MULTI_LOG;
                // ! une cellule finie libere le serveur : ses unites sont retirees 15 s apres, le temps que son verdict
                // soit ecrit ( 70_verdict attend FIN, puis 3 s ). Sans cela les dernieres cellules paieraient la
                // charge de celles qui ont fini.
                [_x] spawn {
                    params ["_k"];
                    sleep 15;
                    private _u = (allUnits + allDeadMen) select { (_x call MULTI_fnc_cellule) == _k };
                    private _v = vehicles select { (_x getVariable ["multi_c", -1]) == _k };
                    { deleteVehicle _x } forEach (_u + _v);
                    (format ["E|cellule_retiree|%1|cellule|%2|unites|%3|vehicules|%4", round (time * 100) / 100, _k, count _u, count _v]) call MULTI_LOG;
                };
            };
        } forEach MULTI_VIVANTES;
        ((count _faites) == (count MULTI_VIVANTES)) || { (time - MULTI_T0) > MULTI_TMAX }
    };
    private _censurees = MULTI_VIVANTES - _faites;
    {
        (format ["E|censure|%1|cellule|%2|depuis_depart|%3|phase|%4", round (time * 100) / 100, _x, round (time - MULTI_T0),
            missionNamespace getVariable [format ["MC%1_PHASE", _x], -1]]) call MULTI_LOG;
    } forEach _censurees;
    sleep 20;   // les derniers verdicts
    MULTI_FINI = true;
    (format ["FINI|%1|cellules|%2|finies|%3|censurees|%4|duree_depuis_depart|%5", round (time * 100) / 100,
        count MULTI_VIVANTES, count _faites, str _censurees, round (time - MULTI_T0)]) call MULTI_LOG;
};
