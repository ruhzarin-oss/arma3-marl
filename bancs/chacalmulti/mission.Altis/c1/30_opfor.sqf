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

private _c = MC1_SITE;

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
if (MC1_PALIER == 9) exitWith {
    MC1_EST_SITE = []; MC1_QRF = []; MC1_GROUPES_EST = [];
    MC1_gQrf = ([east, 1] call MULTI_fnc_groupe); MC1_gGar = grpNull; MC1_gTour = grpNull;
    MC1_gBunk = grpNull; MC1_gHmg = grpNull; MC1_gExt1 = grpNull; MC1_gExt2 = grpNull;
    MC1_gRoute = grpNull; MC1_VEH_ROUTE = objNull; MC1_RONDES = [];
    MC1_GUET = objNull; MC1_VEH_QRF = [];
    MC1_PAL_DELAI = 9999;
    (format ["CHACAL|AVERT|hors_corpus|palier|9|controle_positif_de_l_acte"]) call MC1_LOG;
    (format ["CHACAL|OK|opfor|palier|9|site|0|qrf|0|monde_vide"]) call MC1_LOG;
};

// ! PALIER 4 - LEGER : quatre defenseurs au site, rien d autre. Comble le trou entre le
// palier 0 (16 hommes) et le monde vide (0). C est la ou doit se trouver la bande ou
// l issue est incertaine — ni 0 %, ni 100 %.
// Vrai au seul palier 4 : sert a ecarter les groupes crees sans condition.
MC1_LEGER = (MC1_PALIER == 4);
MC1_PAL_GAR   = [4, 6, 7, 8, 4]  select MC1_PALIER;   // garnison des batiments
MC1_PAL_RONDES= [1, 1, 2, 2, 0]  select MC1_PALIER;   // rondes interieures
MC1_PAL_EXT   = [0, 1, 1, 2, 0]  select MC1_PALIER;   // patrouilles exterieures
MC1_PAL_HMG   = [1, 1, 2, 2, 0]  select MC1_PALIER;   // mitrailleuses servies
// Le job peut forcer ce nombre pour isoler la cause : sur la graine 7 du 08/09, une seule
// piece servie a signe 6 des 9 morts. `select [0, 0]` rend un tableau vide : aucune piece.
if (MC1_HMG_FORCE >= 0) then { MC1_PAL_HMG = MC1_HMG_FORCE };
MC1_PAL_QRF   = [1, 1, 2, 2, 0]  select MC1_PALIER;   // vehicules de reserve
MC1_PAL_DELAI = [180, 120, 75, 45, 9999] select MC1_PALIER; // secondes avant depart de la reserve
MC1_PAL_NVG   = [false, false, true, true, false] select MC1_PALIER; // jumelles a la patrouille de route
MC1_PAL_SKILL = [0.40, 0.47, 0.55, 0.55, 0.40] select MC1_PALIER;
// ! LE JOB PEUT IMPOSER LA RESERVE ( 16/09 ). -1 laisse la table du palier intacte, donc
// tout job anterieur au 16/09 garde exactement le comportement sous lequel son corpus a
// ete mesure. Au palier 4 la table donne QRF = 0 et delai = 9999 : c est la raison pour
// laquelle le bouchon n a jamais rien bloque. Les deux valeurs sont publiees telles
// quelles dans la ligne CHACAL|OK|opfor, donc la trace dit toujours ce qui a ete joue.
if (MC1_QRF_N     >= 0) then { MC1_PAL_QRF   = MC1_QRF_N };
if (MC1_QRF_DELAI >= 0) then { MC1_PAL_DELAI = MC1_QRF_DELAI };

MC1_fnc_kitEst = {
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
MC1_fnc_patrouille = {
    params ["_g", "_p", "_r"];
    if (MC1_LAMBS) then { [_g, _p, _r] call lambs_wp_fnc_taskPatrol }
    else { [_g, _p, _r] call BIS_fnc_taskPatrol };
};
MC1_fnc_garnison = {
    params ["_g", "_p", "_r"];
    if (MC1_LAMBS) then { [_g, _p, _r] call lambs_wp_fnc_taskGarrison }
    else { [_g, _p, _r] call BIS_fnc_taskDefend };
};
MC1_fnc_creer = {
    params ["_g", "_classes", "_p", "_ray", ["_skill", 0.55], ["_nvg", false]];
    {
        private _u = _g createUnit [_x, _p getPos [_ray call MC1_fnc_al, 360 call MC1_fnc_al], [], 0, "NONE"];
        [_u, _skill, _nvg] call MC1_fnc_kitEst;
    } forEach _classes;
    _g
};

// --- 1. la garnison des batiments : elle ne sort pas ---
MC1_gGar = ([east, 1] call MULTI_fnc_groupe);
private _lgar = ["O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_F",
                 "O_Soldier_GL_F","O_medic_F","O_Soldier_LAT_F","O_Soldier_F"];
_lgar resize MC1_PAL_GAR;
[MC1_gGar, _lgar, _c, 30, MC1_PAL_SKILL, false] call MC1_fnc_creer;
MC1_gGar setBehaviour "SAFE"; MC1_gGar setCombatMode "YELLOW"; MC1_gGar allowFleeing 0;
[MC1_gGar, _c, 55] call MC1_fnc_garnison;

// ! INITIALISATIONS HORS GARDE. Les gardes du palier 4 enferment `MC1_RONDES = []`
// et l affectation de MC1_GUET : au palier leger elles ne seraient JAMAIS exécutées,
// et la ligne de journal `count MC1_RONDES` lirait une variable indefinie.
// Une variable citee hors d un bloc doit etre initialisee hors de ce bloc.
MC1_RONDES = []; MC1_GUET = objNull;

// --- 2. le guetteur de la tour : lui voit loin, et lui a des jumelles ---
MC1_gTour = grpNull;
if (!MC1_LEGER) then {
MC1_gTour = ([east, 1] call MULTI_fnc_groupe);
MC1_GUET = MC1_gTour createUnit ["O_Sharpshooter_F", _c getPos [28, 22], [], 0, "NONE"];
[MC1_GUET, 0.8, true] call MC1_fnc_kitEst;
MC1_GUET setUnitPos "UP"; MC1_gTour allowFleeing 0;
if (!isNull MC1_TOUR) then {
    // On NE COUPE PAS "PATH" : mesure du 11/08, ca retire les jambes ( 9 m au
    // lieu de 48 ). Le guetteur est immobile parce qu il est en haut d une tour.
    private _pts = MC1_TOUR buildingPos -1;
    if (count _pts > 1) then { MC1_GUET setPosATL (_pts select ((count _pts) - 1)) };
};
MC1_gTour setBehaviour "AWARE"; MC1_gTour setCombatMode "YELLOW";

// --- 3. les deux rondes interieures : circuit fixe, periode connue ---
MC1_RONDES = [];
{
    private _dep = _x;
    private _g = ([east, 1] call MULTI_fnc_groupe);
    [_g, ["O_Soldier_TL_F","O_Soldier_F","O_Soldier_F"], _c getPos [38, _dep], 6, 0.5, (_forEachIndex == 0)] call MC1_fnc_creer;
    _g setBehaviour "SAFE"; _g setCombatMode "YELLOW"; _g setSpeedMode "LIMITED"; _g allowFleeing 0;
    for "_k" from 0 to 5 do {
        private _w = _g addWaypoint [_c getPos [38, _dep + _k * 60], 4];
        _w setWaypointType "MOVE"; _w setWaypointSpeed "LIMITED"; _w setWaypointBehaviour "SAFE";
        _w setWaypointTimeout [12, 18, 24];       // la releve marque un arret : c est ce qu on compte
    };
    (_g addWaypoint [_c getPos [38, _dep], 4]) setWaypointType "CYCLE";
    MC1_RONDES pushBack _g;
} forEach ([MC1_AZ, MC1_AZ + 180] select [0, MC1_PAL_RONDES]);

// --- 4. les sentinelles de bunker ---
};
MC1_gBunk = grpNull;
if (!MC1_LEGER) then {
MC1_gBunk = ([east, 1] call MULTI_fnc_groupe);
{
    private _u = MC1_gBunk createUnit ["O_Soldier_F", getPosATL _x, [], 0, "NONE"];
    [_u, 0.5, false] call MC1_fnc_kitEst;
    _u setPosATL (getPosATL _x); _u setUnitPos "MIDDLE"; doStop _u;
} forEach MC1_BUNKERS;
MC1_gBunk setBehaviour "SAFE"; MC1_gBunk setCombatMode "YELLOW"; MC1_gBunk allowFleeing 0;

// --- 5. deux mitrailleuses servies, en polaire relative comme le reste ---
};
MC1_gHmg = ([east, 1] call MULTI_fnc_groupe);
{
    _x params ["_hd", "_hg", "_hdir"];
    private _p = _c getPos [_hd, MC1_AZ + _hg];
    private _s = createVehicle ["O_HMG_01_high_F", _p, [], 0, "CAN_COLLIDE"];
    _s setDir (MC1_AZ + _hdir); MC1_PROPS pushBack _s;
    private _g = MC1_gHmg createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    [_g, 0.6, false] call MC1_fnc_kitEst; _g moveInGunner _s;
} forEach ([[45, 75, 100], [47, 340, 345]] select [0, MC1_PAL_HMG]);
MC1_gHmg setBehaviour "SAFE"; MC1_gHmg setCombatMode "YELLOW"; MC1_gHmg allowFleeing 0;

// --- 6. deux patrouilles exterieures, rayons differents ---
MC1_gExt1 = grpNull; MC1_gExt2 = grpNull;
if (MC1_PAL_EXT >= 1) then {
MC1_gExt1 = ([east, 1] call MULTI_fnc_groupe);
[MC1_gExt1, ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_LAT_F","O_Sharpshooter_F"], _c getPos [190, 360 call MC1_fnc_al], 20, 0.55, true] call MC1_fnc_creer;
MC1_gExt1 setBehaviour "SAFE"; MC1_gExt1 setCombatMode "YELLOW"; MC1_gExt1 setSpeedMode "LIMITED"; MC1_gExt1 allowFleeing 0.2;
[MC1_gExt1, _c, 230] call MC1_fnc_patrouille;
};
if (MC1_PAL_EXT >= 2) then {
MC1_gExt2 = ([east, 1] call MULTI_fnc_groupe);
[MC1_gExt2, ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_F","O_Soldier_AR_F"], _c getPos [430, 360 call MC1_fnc_al], 25, 0.5, false] call MC1_fnc_creer;
MC1_gExt2 setBehaviour "SAFE"; MC1_gExt2 setCombatMode "YELLOW"; MC1_gExt2 setSpeedMode "LIMITED"; MC1_gExt2 allowFleeing 0.2;
[MC1_gExt2, _c, 520] call MC1_fnc_patrouille;
};

// --- 7. LA PATROUILLE DE ROUTE. C est elle qui fait de la route un obstacle ---
// Sans elle, franchir la route serait un pas de plus. Avec elle il y a une
// FENETRE, et une fenetre est une decision - donc une chose a apprendre.
MC1_VEH_ROUTE = objNull; MC1_gRoute = grpNull;
if (["O_MRAP_02_hmg_F"] call MC1_fnc_has) then {
    // ! Au palier 4 la route etait vide et la regle de traversee prenait TOUJOURS la branche
    // PATROUILLE_ABSENTE ( 16/09 ). La situation de phase 2 ( niveaux 1 et 3 ) rend le blinde present ;
    // au niveau 0 le palier 4 reste strictement ce qu il etait.
    if (MC1_LEGER && { !(MC1_MENACE_P2 in [1, 3, 4]) }) exitWith {};   // 4 = patrouille seule, posee pres ( oubliee par 16e4b32 )
    MC1_gRoute = ([east, 1] call MULTI_fnc_groupe);
    MC1_VEH_ROUTE = createVehicle ["O_MRAP_02_hmg_F", MC1_ROUTE_A, [], 0, "NONE"];
    // TRANCHE : l equipage d un vehicule de patrouille a des jumelles, c est
    // son metier de voir la nuit. Le choix est publie plus bas.
    { private _u = MC1_gRoute createUnit [_x, MC1_ROUTE_A, [], 0, "NONE"]; [_u, MC1_PAL_SKILL, MC1_PAL_NVG] call MC1_fnc_kitEst; }
        forEach ["O_crew_F","O_crew_F","O_Soldier_F"];
    (units MC1_gRoute) select 0 moveInDriver MC1_VEH_ROUTE;
    (units MC1_gRoute) select 1 moveInGunner MC1_VEH_ROUTE;
    (units MC1_gRoute) select 2 moveInCargo MC1_VEH_ROUTE;
    MC1_gRoute setBehaviour "SAFE"; MC1_gRoute setCombatMode "YELLOW"; MC1_gRoute setSpeedMode "LIMITED";
    { private _w = MC1_gRoute addWaypoint [_x, 8]; _w setWaypointType "MOVE"; _w setWaypointSpeed "LIMITED"; }
        forEach [MC1_ROUTE_B, MC1_ROUTE_A];
    (MC1_gRoute addWaypoint [MC1_ROUTE_A, 8]) setWaypointType "CYCLE";
};

// --- 8. LA RESERVE. Elle dort a 6 km et ne se leve que sur alerte ---
MC1_QRF = [];
MC1_gQrf = ([east, 1] call MULTI_fnc_groupe);
MC1_VEH_QRF = [];
for "_i" from 0 to (MC1_PAL_QRF - 1) do {
    private _v = objNull;
    if (["O_MRAP_02_F"] call MC1_fnc_has) then {
        _v = createVehicle ["O_MRAP_02_F", MC1_QRF_BASE getPos [12 + _i * 14, 90], [], 0, "NONE"];
        MC1_VEH_QRF pushBack _v;
    };
    {
        private _u = MC1_gQrf createUnit [_x, MC1_QRF_BASE, [], 0, "NONE"];
        [_u, 0.6, true] call MC1_fnc_kitEst;
        MC1_QRF pushBack _u;
        if (!isNull _v) then {
            if (_forEachIndex == 0) then { _u moveInDriver _v } else { _u assignAsCargo _v; _u moveInCargo _v };
        };
    } forEach ["O_crew_F","O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_LAT_F","O_Soldier_F"];
};
MC1_gQrf setBehaviour "SAFE"; MC1_gQrf setCombatMode "YELLOW"; MC1_gQrf allowFleeing 0;

MC1_GROUPES_EST = ([MC1_gGar, MC1_gTour, MC1_gBunk, MC1_gHmg, MC1_gExt1, MC1_gExt2] select { !isNull _x }) + MC1_RONDES;
if (!isNull MC1_gRoute) then { MC1_GROUPES_EST pushBack MC1_gRoute };

MC1_EST_SITE = (allUnits select { (_x call MULTI_fnc_cellule) == 1 }) select { side _x == east && { !(_x in MC1_QRF) } };
(format ["CHACAL|OK|opfor|palier|%6|site|%1|qrf|%2|rondes|%3|veh_route|%4|lambs|%5|ext|%7|hmg|%8|delai_qrf|%9|skill|%10",
    count MC1_EST_SITE, count MC1_QRF, count MC1_RONDES,
    (if (isNull MC1_VEH_ROUTE) then {0} else {1}),
    (if (MC1_LAMBS) then {1} else {0}), MC1_PALIER, MC1_PAL_EXT, MC1_PAL_HMG,
    MC1_PAL_DELAI, MC1_PAL_SKILL]) call MC1_LOG;
