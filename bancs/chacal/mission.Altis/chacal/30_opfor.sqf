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

private _c = CHACAL_SITE;

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
if (CHACAL_PALIER == 9) exitWith {
    CHACAL_EST_SITE = []; CHACAL_QRF = []; CHACAL_GROUPES_EST = [];
    CHACAL_gQrf = createGroup east; CHACAL_gGar = grpNull; CHACAL_gTour = grpNull;
    CHACAL_gBunk = grpNull; CHACAL_gHmg = grpNull; CHACAL_gExt1 = grpNull; CHACAL_gExt2 = grpNull;
    CHACAL_gRoute = grpNull; CHACAL_VEH_ROUTE = objNull; CHACAL_RONDES = [];
    CHACAL_GUET = objNull; CHACAL_VEH_QRF = [];
    CHACAL_PAL_DELAI = 9999;
    (format ["CHACAL|AVERT|hors_corpus|palier|9|controle_positif_de_l_acte"]) call CHACAL_LOG;
    (format ["CHACAL|OK|opfor|palier|9|site|0|qrf|0|monde_vide"]) call CHACAL_LOG;
};

// ! PALIER 4 - LEGER : quatre defenseurs au site, rien d autre. Comble le trou entre le
// palier 0 (16 hommes) et le monde vide (0). C est la ou doit se trouver la bande ou
// l issue est incertaine — ni 0 %, ni 100 %.
// Vrai au seul palier 4 : sert a ecarter les groupes crees sans condition.
CHACAL_LEGER = (CHACAL_PALIER == 4);
CHACAL_PAL_GAR   = [4, 6, 7, 8, 4]  select CHACAL_PALIER;   // garnison des batiments
CHACAL_PAL_RONDES= [1, 1, 2, 2, 0]  select CHACAL_PALIER;   // rondes interieures
CHACAL_PAL_EXT   = [0, 1, 1, 2, 0]  select CHACAL_PALIER;   // patrouilles exterieures
CHACAL_PAL_HMG   = [1, 1, 2, 2, 0]  select CHACAL_PALIER;   // mitrailleuses servies
// Le job peut forcer ce nombre pour isoler la cause : sur la graine 7 du 08/09, une seule
// piece servie a signe 6 des 9 morts. `select [0, 0]` rend un tableau vide : aucune piece.
if (CHACAL_HMG_FORCE >= 0) then { CHACAL_PAL_HMG = CHACAL_HMG_FORCE };
CHACAL_PAL_QRF   = [1, 1, 2, 2, 0]  select CHACAL_PALIER;   // vehicules de reserve
CHACAL_PAL_DELAI = [180, 120, 75, 45, 9999] select CHACAL_PALIER; // secondes avant depart de la reserve
CHACAL_PAL_NVG   = [false, false, true, true, false] select CHACAL_PALIER; // jumelles a la patrouille de route
CHACAL_PAL_SKILL = [0.40, 0.47, 0.55, 0.55, 0.40] select CHACAL_PALIER;

CHACAL_fnc_kitEst = {
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
CHACAL_fnc_patrouille = {
    params ["_g", "_p", "_r"];
    if (CHACAL_LAMBS) then { [_g, _p, _r] call lambs_wp_fnc_taskPatrol }
    else { [_g, _p, _r] call BIS_fnc_taskPatrol };
};
CHACAL_fnc_garnison = {
    params ["_g", "_p", "_r"];
    if (CHACAL_LAMBS) then { [_g, _p, _r] call lambs_wp_fnc_taskGarrison }
    else { [_g, _p, _r] call BIS_fnc_taskDefend };
};
CHACAL_fnc_creer = {
    params ["_g", "_classes", "_p", "_ray", ["_skill", 0.55], ["_nvg", false]];
    {
        private _u = _g createUnit [_x, _p getPos [_ray call CHACAL_fnc_al, 360 call CHACAL_fnc_al], [], 0, "NONE"];
        [_u, _skill, _nvg] call CHACAL_fnc_kitEst;
    } forEach _classes;
    _g
};

// --- 1. la garnison des batiments : elle ne sort pas ---
CHACAL_gGar = createGroup east;
private _lgar = ["O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_F",
                 "O_Soldier_GL_F","O_medic_F","O_Soldier_LAT_F","O_Soldier_F"];
_lgar resize CHACAL_PAL_GAR;
[CHACAL_gGar, _lgar, _c, 30, CHACAL_PAL_SKILL, false] call CHACAL_fnc_creer;
CHACAL_gGar setBehaviour "SAFE"; CHACAL_gGar setCombatMode "YELLOW"; CHACAL_gGar allowFleeing 0;
[CHACAL_gGar, _c, 55] call CHACAL_fnc_garnison;

// --- 2. le guetteur de la tour : lui voit loin, et lui a des jumelles ---
CHACAL_gTour = grpNull;
if (!CHACAL_LEGER) then {
CHACAL_gTour = createGroup east;
CHACAL_GUET = CHACAL_gTour createUnit ["O_Sharpshooter_F", _c getPos [28, 22], [], 0, "NONE"];
[CHACAL_GUET, 0.8, true] call CHACAL_fnc_kitEst;
CHACAL_GUET setUnitPos "UP"; CHACAL_gTour allowFleeing 0;
if (!isNull CHACAL_TOUR) then {
    // On NE COUPE PAS "PATH" : mesure du 11/08, ca retire les jambes ( 9 m au
    // lieu de 48 ). Le guetteur est immobile parce qu il est en haut d une tour.
    private _pts = CHACAL_TOUR buildingPos -1;
    if (count _pts > 1) then { CHACAL_GUET setPosATL (_pts select ((count _pts) - 1)) };
};
CHACAL_gTour setBehaviour "AWARE"; CHACAL_gTour setCombatMode "YELLOW";

// --- 3. les deux rondes interieures : circuit fixe, periode connue ---
CHACAL_RONDES = [];
{
    private _dep = _x;
    private _g = createGroup east;
    [_g, ["O_Soldier_TL_F","O_Soldier_F","O_Soldier_F"], _c getPos [38, _dep], 6, 0.5, (_forEachIndex == 0)] call CHACAL_fnc_creer;
    _g setBehaviour "SAFE"; _g setCombatMode "YELLOW"; _g setSpeedMode "LIMITED"; _g allowFleeing 0;
    for "_k" from 0 to 5 do {
        private _w = _g addWaypoint [_c getPos [38, _dep + _k * 60], 4];
        _w setWaypointType "MOVE"; _w setWaypointSpeed "LIMITED"; _w setWaypointBehaviour "SAFE";
        _w setWaypointTimeout [12, 18, 24];       // la releve marque un arret : c est ce qu on compte
    };
    (_g addWaypoint [_c getPos [38, _dep], 4]) setWaypointType "CYCLE";
    CHACAL_RONDES pushBack _g;
} forEach ([CHACAL_AZ, CHACAL_AZ + 180] select [0, CHACAL_PAL_RONDES]);

// --- 4. les sentinelles de bunker ---
};
CHACAL_gBunk = grpNull;
if (!CHACAL_LEGER) then {
CHACAL_gBunk = createGroup east;
{
    private _u = CHACAL_gBunk createUnit ["O_Soldier_F", getPosATL _x, [], 0, "NONE"];
    [_u, 0.5, false] call CHACAL_fnc_kitEst;
    _u setPosATL (getPosATL _x); _u setUnitPos "MIDDLE"; doStop _u;
} forEach CHACAL_BUNKERS;
CHACAL_gBunk setBehaviour "SAFE"; CHACAL_gBunk setCombatMode "YELLOW"; CHACAL_gBunk allowFleeing 0;

// --- 5. deux mitrailleuses servies, en polaire relative comme le reste ---
};
CHACAL_gHmg = createGroup east;
{
    _x params ["_hd", "_hg", "_hdir"];
    private _p = _c getPos [_hd, CHACAL_AZ + _hg];
    private _s = createVehicle ["O_HMG_01_high_F", _p, [], 0, "CAN_COLLIDE"];
    _s setDir (CHACAL_AZ + _hdir); CHACAL_PROPS pushBack _s;
    private _g = CHACAL_gHmg createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    [_g, 0.6, false] call CHACAL_fnc_kitEst; _g moveInGunner _s;
} forEach ([[45, 75, 100], [47, 340, 345]] select [0, CHACAL_PAL_HMG]);
CHACAL_gHmg setBehaviour "SAFE"; CHACAL_gHmg setCombatMode "YELLOW"; CHACAL_gHmg allowFleeing 0;

// --- 6. deux patrouilles exterieures, rayons differents ---
CHACAL_gExt1 = grpNull; CHACAL_gExt2 = grpNull;
if (CHACAL_PAL_EXT >= 1) then {
CHACAL_gExt1 = createGroup east;
[CHACAL_gExt1, ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_LAT_F","O_Sharpshooter_F"], _c getPos [190, 360 call CHACAL_fnc_al], 20, 0.55, true] call CHACAL_fnc_creer;
CHACAL_gExt1 setBehaviour "SAFE"; CHACAL_gExt1 setCombatMode "YELLOW"; CHACAL_gExt1 setSpeedMode "LIMITED"; CHACAL_gExt1 allowFleeing 0.2;
[CHACAL_gExt1, _c, 230] call CHACAL_fnc_patrouille;
};
if (CHACAL_PAL_EXT >= 2) then {
CHACAL_gExt2 = createGroup east;
[CHACAL_gExt2, ["O_Soldier_SL_F","O_Soldier_F","O_Soldier_F","O_Soldier_AR_F"], _c getPos [430, 360 call CHACAL_fnc_al], 25, 0.5, false] call CHACAL_fnc_creer;
CHACAL_gExt2 setBehaviour "SAFE"; CHACAL_gExt2 setCombatMode "YELLOW"; CHACAL_gExt2 setSpeedMode "LIMITED"; CHACAL_gExt2 allowFleeing 0.2;
[CHACAL_gExt2, _c, 520] call CHACAL_fnc_patrouille;
};

// --- 7. LA PATROUILLE DE ROUTE. C est elle qui fait de la route un obstacle ---
// Sans elle, franchir la route serait un pas de plus. Avec elle il y a une
// FENETRE, et une fenetre est une decision - donc une chose a apprendre.
CHACAL_VEH_ROUTE = objNull; CHACAL_gRoute = grpNull;
if (["O_MRAP_02_hmg_F"] call CHACAL_fnc_has) then {
    if (CHACAL_LEGER) exitWith {};
    CHACAL_gRoute = createGroup east;
    CHACAL_VEH_ROUTE = createVehicle ["O_MRAP_02_hmg_F", CHACAL_ROUTE_A, [], 0, "NONE"];
    // TRANCHE : l equipage d un vehicule de patrouille a des jumelles, c est
    // son metier de voir la nuit. Le choix est publie plus bas.
    { private _u = CHACAL_gRoute createUnit [_x, CHACAL_ROUTE_A, [], 0, "NONE"]; [_u, CHACAL_PAL_SKILL, CHACAL_PAL_NVG] call CHACAL_fnc_kitEst; }
        forEach ["O_crew_F","O_crew_F","O_Soldier_F"];
    (units CHACAL_gRoute) select 0 moveInDriver CHACAL_VEH_ROUTE;
    (units CHACAL_gRoute) select 1 moveInGunner CHACAL_VEH_ROUTE;
    (units CHACAL_gRoute) select 2 moveInCargo CHACAL_VEH_ROUTE;
    CHACAL_gRoute setBehaviour "SAFE"; CHACAL_gRoute setCombatMode "YELLOW"; CHACAL_gRoute setSpeedMode "LIMITED";
    { private _w = CHACAL_gRoute addWaypoint [_x, 8]; _w setWaypointType "MOVE"; _w setWaypointSpeed "LIMITED"; }
        forEach [CHACAL_ROUTE_B, CHACAL_ROUTE_A];
    (CHACAL_gRoute addWaypoint [CHACAL_ROUTE_A, 8]) setWaypointType "CYCLE";
};

// --- 8. LA RESERVE. Elle dort a 6 km et ne se leve que sur alerte ---
CHACAL_QRF = [];
CHACAL_gQrf = createGroup east;
CHACAL_VEH_QRF = [];
for "_i" from 0 to (CHACAL_PAL_QRF - 1) do {
    private _v = objNull;
    if (["O_MRAP_02_F"] call CHACAL_fnc_has) then {
        _v = createVehicle ["O_MRAP_02_F", CHACAL_QRF_BASE getPos [12 + _i * 14, 90], [], 0, "NONE"];
        CHACAL_VEH_QRF pushBack _v;
    };
    {
        private _u = CHACAL_gQrf createUnit [_x, CHACAL_QRF_BASE, [], 0, "NONE"];
        [_u, 0.6, true] call CHACAL_fnc_kitEst;
        CHACAL_QRF pushBack _u;
        if (!isNull _v) then {
            if (_forEachIndex == 0) then { _u moveInDriver _v } else { _u assignAsCargo _v; _u moveInCargo _v };
        };
    } forEach ["O_crew_F","O_Soldier_TL_F","O_Soldier_AR_F","O_Soldier_F","O_Soldier_LAT_F","O_Soldier_F"];
};
CHACAL_gQrf setBehaviour "SAFE"; CHACAL_gQrf setCombatMode "YELLOW"; CHACAL_gQrf allowFleeing 0;

CHACAL_GROUPES_EST = ([CHACAL_gGar, CHACAL_gTour, CHACAL_gBunk, CHACAL_gHmg, CHACAL_gExt1, CHACAL_gExt2] select { !isNull _x }) + CHACAL_RONDES;
if (!isNull CHACAL_gRoute) then { CHACAL_GROUPES_EST pushBack CHACAL_gRoute };

CHACAL_EST_SITE = allUnits select { side _x == east && { !(_x in CHACAL_QRF) } };
(format ["CHACAL|OK|opfor|palier|%6|site|%1|qrf|%2|rondes|%3|veh_route|%4|lambs|%5|ext|%7|hmg|%8|delai_qrf|%9|skill|%10",
    count CHACAL_EST_SITE, count CHACAL_QRF, count CHACAL_RONDES,
    (if (isNull CHACAL_VEH_ROUTE) then {0} else {1}),
    (if (CHACAL_LAMBS) then {1} else {0}), CHACAL_PALIER, CHACAL_PAL_EXT, CHACAL_PAL_HMG,
    CHACAL_PAL_DELAI, CHACAL_PAL_SKILL]) call CHACAL_LOG;
