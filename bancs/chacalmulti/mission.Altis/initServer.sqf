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

// --- 2. partir ensemble ---
MULTI_T0 = time;
MULTI_DEPART = true;
(format ["OK|depart|%1|cellules|%2|unites|%3|groupes|%4", round (time * 100) / 100, MULTI_VIVANTES, count allUnits, count allGroups]) call MULTI_LOG;

// --- 3b. l'independance : ce que chaque chef de groupe CONNAIT d'une autre cellule, toutes les 2 s ---
// nearTargets rend la connaissance du groupe du chef, amis compris. Une entree dont la cellule differe de celle du
// chef est un CROISEMENT : ennemi ( fuite a tolerance zero ) ou ami ( proximite, a lire ). La sonde porte deux
// cellules a elle, 100 ( l'observateur ) et 101 ( la cible ) : chaque fois qu'elle est connue, ce journal DOIT la
// voir. C'est son controle positif.
[] spawn {
    while { !MULTI_FINI } do {
        private _t = round (time * 100) / 100;
        private _chefs = 0; private _ennemis = []; private _amis = []; private _ctrl = 0;
        {
            private _l = leader _x;
            if (!isNull _l && { alive _l }) then {
                private _c = _l call MULTI_fnc_cellule;
                if (_c >= 1) then {
                    _chefs = _chefs + 1;
                    private _sl = side (group _l);
                    {
                        private _o = _x select 4;
                        if (!isNull _o) then {
                            private _co = _o call MULTI_fnc_cellule;
                            if (_co >= 1 && { _co != _c }) then {
                                if ((_c == 100) && { _co == 101 }) then { _ctrl = _ctrl + 1 } else {
                                    private _e = [_c, _co, round (_l distance2D _o)];
                                    if ((_x select 2) != _sl) then { _ennemis pushBack _e } else { _amis pushBack _e };
                                };
                            };
                        };
                    } forEach (_l nearTargets 30000);
                };
            };
        } forEach allGroups;
        (format ["E|croise|%1|chefs|%2|ennemis|%3|amis|%4|controle_sonde|%5|detail_ennemis|%6|detail_amis|%7", _t, _chefs,
            count _ennemis, count _amis, _ctrl, str (_ennemis select [0, 6]), str (_amis select [0, 6])]) call MULTI_LOG;
        sleep 2;
    };
};

// --- 3c. la sonde de connaissance : debout, 150 m, nuit, regard pose - la mesure du banc de seuil du 18/09 ---
// Hors de toute cellule ( MULTI_ESPACEMENT de toutes les emprises ). Un cycle par minute : un observateur neuf, une
// cible neuve, et le delai jusqu'a ce que le groupe de l'observateur la connaisse.
if (MULTI_SONDE == 1) then {
    [] spawn {
        private _n = 0;
        sleep 10;
        while { !MULTI_FINI } do {
            _n = _n + 1;
            private _p = []; private _q = []; private _essais = 0;
            while { (count _p == 0) && { _essais < 300 } } do {
                _essais = _essais + 1;
                private _c = [3000 + random 24000, 3000 + random 24000, 0];
                if (!surfaceIsWater _c && { [_c, 0] call MULTI_fnc_loin } && { count (nearestObjects [_c, ["House"], 60]) == 0 }) then {
                    private _oe = [_c select 0, _c select 1, (getTerrainHeightASL _c) + 1.7];
                    {
                        private _t = _c getPos [150, _x];
                        if (!surfaceIsWater _t) then {
                            private _tt = [_t select 0, _t select 1, (getTerrainHeightASL _t) + 1.6];
                            if ((count (lineIntersectsSurfaces [_oe, _tt, objNull, objNull, true, 1, "VIEW", "VIEW"])) == 0) exitWith { _q = _t };
                        };
                    } forEach [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340];
                    if (count _q > 0) then { _p = _c };
                };
            };
            if (count _p == 0) then {
                (format ["E|sonde|%1|cycle|%2|introuvable|%3", round (time * 100) / 100, _n, _essais]) call MULTI_LOG;
                sleep 60;
            } else {
                private _go = [west, 100] call MULTI_fnc_groupe;
                private _o = _go createUnit ["B_recon_TL_F", _p, [], 0, "CAN_COLLIDE"];
                _o setSkill ["spotDistance", 0.75]; _o setSkill ["spotTime", 0.8];
                if ((hmd _o) == "") then { _o linkItem "NVGoggles" };
                _o allowDamage false; _go setBehaviour "STEALTH"; _go setCombatMode "GREEN"; doStop _o;
                sleep 5;
                private _gc = [east, 101] call MULTI_fnc_groupe;
                { private _u = _gc createUnit [_x, _q, [], 3, "NONE"]; _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE"; _u setUnitPos "UP"; _u allowDamage false } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
                _gc setCombatMode "BLUE"; _gc setBehaviour "SAFE";
                private _cible = leader _gc;
                _o doWatch _cible;
                private _d = round (_o distance2D _cible);
                MULTI_SONDE_ACTIVE = [_o, _cible, time, _n, _d];
                private _t0 = time;
                waitUntil { sleep 1; (count MULTI_SONDE_ACTIVE == 0) || { (time - _t0) > 45 } || MULTI_FINI };
                if (count MULTI_SONDE_ACTIVE > 0) then {
                    MULTI_SONDE_ACTIVE = [];
                    (format ["E|sonde|%1|cycle|%2|connue|0|delai|-1|distance|%3|fps|%4", round (time * 100) / 100, _n, _d, round diag_fps]) call MULTI_LOG;
                };
                sleep 4;   // le journal croise doit avoir le temps de voir la connaissance
                { deleteVehicle _x } forEach (units _go + units _gc);
                deleteGroup _go; deleteGroup _gc;
                sleep 10;
            };
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
