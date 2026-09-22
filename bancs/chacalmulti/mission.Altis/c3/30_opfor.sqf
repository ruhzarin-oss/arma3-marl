// =====================================================================
// CHACAL - LA GARNISON. Une trentaine d hommes sur le site, douze en reserve.
//
// Le partage est explicite et c est tout le sujet du banc :
//   . LE SCRIPT donne le PLAN - qui garde quoi, quelle ronde, quel horaire.
//   . LAMBS donne la REACTION au contact - suppression, couvert, flanc, CQB.
// Un corpus qui melange les deux ne sait plus ce qu il enseigne.
//
// Les rondes interieures sont des CIRCUITS FIXES a periode connue : sans cela
// la phase d observation n aurait rien a compter.
// =====================================================================

private _c = MC3_SITE;

// ! LE PALIER DE FORCE ( 04/09 ). Le premier episode complet de nuit s est
// solde par 0 charge, 2 survivants sur 10 et 17 rouges tues : dix hommes qui
// entrent contre trente et un ne ressortent pas. On ne rend pas la mission
// gagnable d office - ce serait refaire le vice qu on corrige depuis deux
// jours, une mesure qui ne sait plus echouer - on la desserre PAR PALIERS pour
// chercher le seuil ou l issue devient incertaine.
//
// Chaque palier retire des choses COHERENTES entre elles, jamais un simple
// compteur : des hommes, une ronde, une patrouille exterieure, des jumelles,
// de la reserve et de la reactivite. La composition reelle est publiee.
// ! LE PALIER 9 EST LE CONTROLE POSITIF DE L ACTE ( Fable, 05/09 ).
// `charge_posee` n apparait dans AUCUN des vingt-cinq episodes archives :
// l enregistreur sait detecter une mort, un tir, une vue - il n a jamais montre
// qu il sait detecter l acte qui DEFINIT la mission. Regle 16.
// Au palier 9 il n y a pas un seul ennemi. La mission doit alors rendre
// SUCCES 3/3 avec six exfiltres. Si elle n y arrive pas, aucune nuit ne tourne :
// ce n est pas le monde qui resiste, c est la couture qui est cassee.
if (MC3_PALIER == 9) exitWith {
    MC3_EST_SITE = []; MC3_QRF = []; MC3_GROUPES_EST = [];
    MC3_gQrf = ([east, 3] call MULTI_fnc_groupe); MC3_gGar = grpNull; MC3_gTour = grpNull;
    MC3_gBunk = grpNull; MC3_gHmg = grpNull; MC3_gExt1 = grpNull; MC3_gExt2 = grpNull;
    MC3_gRoute = grpNull; MC3_VEH_ROUTE = objNull; MC3_RONDES = [];
    MC3_GUET = objNull; MC3_VEH_QRF = [];
    MC3_PAL_DELAI = 9999;
    (format ["CHACAL|AVERT|hors_corpus|palier|9|controle_positif_de_l_acte"]) call MC3_LOG;
    (format ["CHACAL|OK|opfor|palier|9|site|0|qrf|0|monde_vide"]) call MC3_LOG;
};

// ! PALIER 4 - LEGER : quatre defenseurs au site, rien d autre. Comble le trou entre le
// palier 0 (16 hommes) et le monde vide (0). C est la ou doit se trouver la bande ou
// l issue est incertaine — ni 0 %, ni 100 %.
// Vrai au seul palier 4 : sert a ecarter les groupes crees sans condition.
MC3_LEGER = (MC3_PALIER == 4);
MC3_PAL_GAR   = [4, 6, 7, 8, 4]  select MC3_PALIER;   // garnison des batiments
MC3_PAL_RONDES= [1, 1, 2, 2, 0]  select MC3_PALIER;   // rondes interieures
MC3_PAL_EXT   = [0, 1, 1, 2, 0]  select MC3_PALIER;   // patrouilles exterieures
MC3_PAL_HMG   = [1, 1, 2, 2, 0]  select MC3_PALIER;   // mitrailleuses servies
// Le job peut forcer ce nombre pour isoler la cause : sur la graine 7 du 08/09, une seule
// piece servie a signe 6 des 9 morts. `select [0, 0]` rend un tableau vide : aucune piece.
if (MC3_HMG_FORCE >= 0) then { MC3_PAL_HMG = MC3_HMG_FORCE };
MC3_PAL_QRF   = [1, 1, 2, 2, 0]  select MC3_PALIER;   // vehicules de reserve
MC3_PAL_DELAI = [180, 120, 75, 45, 9999] select MC3_PALIER; // secondes avant depart de la reserve
MC3_PAL_NVG   = [false, false, true, true, false] select MC3_PALIER; // jumelles a la patrouille de route
MC3_PAL_SKILL = [0.40, 0.47, 0.55, 0.55, 0.40] select MC3_PALIER;
// ! LE JOB PEUT IMPOSER LA RESERVE ( 16/09 ). -1 laisse la table du palier intacte, donc
// tout job anterieur au 16/09 garde exactement le comportement sous lequel son corpus a
// ete mesure. Au palier 4 la table donne QRF = 0 et delai = 9999 : c est la raison pour
// laquelle le bouchon n a jamais rien bloque. Les deux valeurs sont publiees telles
// quelles dans la ligne CHACAL|OK|opfor, donc la trace dit toujours ce qui a ete joue.
if (MC3_QRF_N     >= 0) then { MC3_PAL_QRF   = MC3_QRF_N };
if (MC3_QRF_DELAI >= 0) then { MC3_PAL_DELAI = MC3_QRF_DELAI };

MC3_fnc_kitEst = {
    params ["_u", ["_skill", 0.55], ["_nvg", false]];
    _u setSkill ["spotDistance", _skill];
    _u setSkill ["spotTime", _skill];
    _u setSkill ["aimingAccuracy", _skill * 0.6];
    _u setSkill ["aimingSpeed", _skill * 0.8];
    _u setSkill ["courage", 0.8];
    _u setSkill ["commanding", 0.8];
    // La nuit est le seul avantage des dix. On ne le retire pas en equipant
    // toute la garnison : jumelles au guetteur, aux chefs, a la patrouille de
    // route et a la reserve. Ce choix est PUBLIE dans la ligne OK.
    if (_nvg) then { _u linkItem "NVGoggles_OPFOR" }
    else { if ((hmd _u) != "") then { _u unlinkItem (hmd _u) } };
};
MC3_fnc_patrouille = {
    params ["_g", "_p", "_r"];
    if (MC3_LAMBS) then { [_g, _p, _r] call lambs_wp_fnc_taskPatrol }
    else { [_g, _p, _r] call BIS_fnc_taskPatrol };
};
MC3_fnc_garnison = {
    params ["_g", "_p", "_r"];
    if (MC3_LAMBS) then { [_g, _p, _r] call lambs_wp_fnc_taskGarrison }
    else { [_g, _p, _r] call BIS_fnc_taskDefend };
};
MC3_fnc_creer = {
    params ["_g", "_classes", "_p", "_ray", ["_skill", 0.55], ["_nvg", false]];
    {
        private _u = _g createUnit [_x, _p getPos [_ray call MC3_fnc_al, 360 call MC3_fnc_al], [], 0, "NONE"];
        [_u, _skill, _nvg] call MC3_fnc_kitEst;
    } forEach _classes;
    _g
};

// --- 1. la garnison des batiments : elle ne sort pas ---
MC3_gGar = ([east, 3] call MULTI_fnc_groupe);
private _lgar = ["O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_F",
                 "O_Soldier_GL_F","O_medic_F","O_Soldier_LAT_F","O_Soldier_F"];
_lgar resize MC3_PAL_GAR;
[MC3_gGar, _lgar, _c, 30, MC3_PAL_SKILL, false] call MC3_fnc_creer;
MC3_gGar setBehaviour "SAFE"; MC3_gGar setCombatMode "YELLOW"; MC3_gGar allowFleeing 0;
[MC3_gGar, _c, 55] call MC3_fnc_garnison;

// ! INITIALISATIONS HORS GARDE. Les gardes du palier 4 enferment `MC3_RONDES = []`
// et l affectation de MC3_GUET : au palier leger elles ne seraient JAMAIS exécutées,
// et la ligne de journal `count MC3_RONDES` lirait une variable indefinie.
// Une variable citee hors d un bloc doit etre initialisee hors de ce bloc.
MC3_RONDES = []; MC3_GUET = objNull;

// --- 2. le guetteur de la tour : lui voit loin, et lui a des jumelles ---
MC3_gTour = grpNull;
if (!MC3_LEGER) then {
MC3_gTour = ([east, 3] call MULTI_fnc_groupe);
MC3_GUET = MC3_gTour createUnit ["O_Sharpshooter_F", _c getPos [28, 22], [], 0, "NONE"];
[MC3_GUET, 0.8, true] call MC3_fnc_kitEst;
MC3_GUET setUnitPos "UP"; MC3_gTour allowFleeing 0;
if (!isNull MC3_TOUR) then {
    // On NE COUPE PAS "PATH" : mesure du 11/08, ca retire les jambes ( 9 m au
    // lieu de 48 ). Le guetteur est immobile parce qu il est en haut d une tour.
    private _pts = MC3_TOUR buildingPos -1;
    if (count _pts > 1) then { MC3_GUET setPosATL (_pts select ((count _pts) - 1)) };
};
MC3_gTour setBehaviour "AWARE"; MC3_gTour setCombatMode "YELLOW";

// --- 3. les deux rondes interieures : circuit fixe, periode connue ---
MC3_RONDES = [];
{
    private _dep = _x;
    private _g = ([east, 3] call MULTI_fnc_groupe);
    [_g, ["O_Soldier_TL_F","O_Soldier_F","O_Soldier_F"], _c getPos [38, _dep], 6, 0.5, (_forEachIndex == 0)] call MC3_fnc_creer;
    _g setBehaviour "SAFE"; _g setCombatMode "YELLOW"; _g setSpeedMode "LIMITED"; _g allowFleeing 0;
    for "_k" from 0 to 5 do {
        private _w = _g addWaypoint [_c getPos [38, _dep + _k * 60], 4];
        _w setWaypointType "MOVE"; _w setWaypointSpeed "LIMITED"; _w setWaypointBehaviour "SAFE";
        _w setWaypointTimeout [12, 18, 24];       // la releve marque un arret : c est ce qu on compte
    };
    (_g addWaypoint [_c getPos [38, _dep], 4]) setWaypointType "CYCLE";
    MC3_RONDES pushBack _g;
} forEach ([MC3_AZ, MC3_AZ + 180] select [0, MC3_PAL_RONDES]);

// --- 4. les sentinelles de bunker ---
};
MC3_gBunk = grpNull;
if (!MC3_LEGER) then {
MC3_gBunk = ([east, 3] call MULTI_fnc_groupe);
{
    private _u = MC3_gBunk createUnit ["O_Soldier_F", getPosATL _x, [], 0, "NONE"];
    [_u, 0.5, false] call MC3_fnc_kitEst;
    _u setPosATL (getPosATL _x); _u setUnitPos "MIDDLE"; doStop _u;
} forEach MC3_BUNKERS;
MC3_gBunk setBehaviour "SAFE"; MC3_gBunk setCombatMode "YELLOW"; MC3_gBunk allowFleeing 0;

// --- 5. deux mitrailleuses servies, en polaire relative comme le reste ---
};
MC3_gHmg = ([east, 3] call MULTI_fnc_groupe);
{
    _x params ["_hd", "_hg", "_hdir"];
    private _p = _c getPos [_hd, MC3_AZ + _hg];
    private _s = createVehicle ["O_HMG_01_high_F", _p, [], 0, "CAN_COLLIDE"];
    _s setDir (MC3_AZ + _hdir); MC3_PROPS pushBack _s;
    private _g = MC3_gHmg createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    [_g, 0.6, false] call MC3_fnc_kitEst; _g moveInGunner _s;
} forEach ([[45, 75, 100], [47, 340, 345]] select [0, MC3_PAL_HMG]);
MC3_gHmg setBehaviour "SAFE"; MC3_gHmg setCombatMode "YELLOW"; MC3_gHmg allowFleeing 0;

// --- 6. deux patrouilles exterieures, rayons differents ---
MC3_gExt1 = grpNull; MC3_gExt2 = grpNull;
if (MC3_PAL_EXT >= 1) then {
MC3_gExt1 = ([east, 3] call MULTI_fnc_groupe);
[MC3_gExt1, ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_LAT_F","O_Sharpshooter_F"], _c getPos [190, 360 call MC3_fnc_al], 20, 0.55, true] call MC3_fnc_creer;
MC3_gExt1 setBehaviour "SAFE"; MC3_gExt1 setCombatMode "YELLOW"; MC3_gExt1 setSpeedMode "LIMITED"; MC3_gExt1 allowFleeing 0.2;
[MC3_gExt1, _c, 230] call MC3_fnc_patrouille;
};
if (MC3_PAL_EXT >= 2) then {
MC3_gExt2 = ([east, 3] call MULTI_fnc_groupe);
[MC3_gExt2, ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_F","O_Soldier_AR_F"], _c getPos [430, 360 call MC3_fnc_al], 25, 0.5, false] call MC3_fnc_creer;
MC3_gExt2 setBehaviour "SAFE"; MC3_gExt2 setCombatMode "YELLOW"; MC3_gExt2 setSpeedMode "LIMITED"; MC3_gExt2 allowFleeing 0.2;
[MC3_gExt2, _c, 520] call MC3_fnc_patrouille;
};

// --- 7. LA PATROUILLE DE ROUTE. C est elle qui fait de la route un obstacle ---
// Sans elle, franchir la route serait un pas de plus. Avec elle il y a une
// FENETRE, et une fenetre est une decision - donc une chose a apprendre.
MC3_VEH_ROUTE = objNull; MC3_gRoute = grpNull;
if (["O_MRAP_02_hmg_F"] call MC3_fnc_has) then {
    // ! Au palier 4 la route etait vide et la regle de traversee prenait TOUJOURS la branche
    // PATROUILLE_ABSENTE ( 16/09 ). La situation de phase 2 ( niveaux 1 et 3 ) rend le blinde present ;
    // au niveau 0 le palier 4 reste strictement ce qu il etait.
    if (MC3_LEGER && { !(MC3_MENACE_P2 in [1, 3, 4]) }) exitWith {};   // 4 = patrouille seule, posee pres ( oubliee par 16e4b32 )
    MC3_gRoute = ([east, 3] call MULTI_fnc_groupe);
    MC3_VEH_ROUTE = createVehicle ["O_MRAP_02_hmg_F", MC3_ROUTE_A, [], 0, "NONE"];
    // TRANCHE : l equipage d un vehicule de patrouille a des jumelles, c est
    // son metier de voir la nuit. Le choix est publie plus bas.
    { private _u = MC3_gRoute createUnit [_x, MC3_ROUTE_A, [], 0, "NONE"]; [_u, MC3_PAL_SKILL, MC3_PAL_NVG] call MC3_fnc_kitEst; }
        forEach ["O_crew_F","O_crew_F","O_Soldier_F"];
    (units MC3_gRoute) select 0 moveInDriver MC3_VEH_ROUTE;
    (units MC3_gRoute) select 1 moveInGunner MC3_VEH_ROUTE;
    (units MC3_gRoute) select 2 moveInCargo MC3_VEH_ROUTE;
    MC3_gRoute setBehaviour "SAFE"; MC3_gRoute setCombatMode "YELLOW"; MC3_gRoute setSpeedMode "LIMITED";
    { private _w = MC3_gRoute addWaypoint [_x, 8]; _w setWaypointType "MOVE"; _w setWaypointSpeed "LIMITED"; }
        forEach [MC3_ROUTE_B, MC3_ROUTE_A];
    (MC3_gRoute addWaypoint [MC3_ROUTE_A, 8]) setWaypointType "CYCLE";
};

// --- 8. LA RESERVE. Elle dort a 6 km et ne se leve que sur alerte ---
MC3_QRF = [];
MC3_gQrf = ([east, 3] call MULTI_fnc_groupe);
MC3_VEH_QRF = [];
for "_i" from 0 to (MC3_PAL_QRF - 1) do {
    private _v = objNull;
    if (["O_MRAP_02_F"] call MC3_fnc_has) then {
        _v = createVehicle ["O_MRAP_02_F", MC3_QRF_BASE getPos [12 + _i * 14, 90], [], 0, "NONE"];
        MC3_VEH_QRF pushBack _v;
    };
    {
        private _u = MC3_gQrf createUnit [_x, MC3_QRF_BASE, [], 0, "NONE"];
        [_u, 0.6, true] call MC3_fnc_kitEst;
        MC3_QRF pushBack _u;
        if (!isNull _v) then {
            if (_forEachIndex == 0) then { _u moveInDriver _v } else { _u assignAsCargo _v; _u moveInCargo _v };
        };
    } forEach ["O_crew_F","O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_LAT_F","O_Soldier_F"];
};
MC3_gQrf setBehaviour "SAFE"; MC3_gQrf setCombatMode "YELLOW"; MC3_gQrf allowFleeing 0;

MC3_GROUPES_EST = ([MC3_gGar, MC3_gTour, MC3_gBunk, MC3_gHmg, MC3_gExt1, MC3_gExt2] select { !isNull _x }) + MC3_RONDES;
if (!isNull MC3_gRoute) then { MC3_GROUPES_EST pushBack MC3_gRoute };

MC3_EST_SITE = (allUnits select { (_x call MULTI_fnc_cellule) == 3 }) select { side _x == east && { !(_x in MC3_QRF) } };
(format ["CHACAL|OK|opfor|palier|%6|site|%1|qrf|%2|rondes|%3|veh_route|%4|lambs|%5|ext|%7|hmg|%8|delai_qrf|%9|skill|%10",
    count MC3_EST_SITE, count MC3_QRF, count MC3_RONDES,
    (if (isNull MC3_VEH_ROUTE) then {0} else {1}),
    (if (MC3_LAMBS) then {1} else {0}), MC3_PALIER, MC3_PAL_EXT, MC3_PAL_HMG,
    MC3_PAL_DELAI, MC3_PAL_SKILL]) call MC3_LOG;
