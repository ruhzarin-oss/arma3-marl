// =====================================================================
// MONDE - le CORPS du pays. Le cerveau ( Python, paquet monde/ du depot ) decide ; cette mission execute ses ordres
// et lui rapporte ce qu elle voit. Rien ici ne decide de la vie d un habitant.
//
// Le pont : l extension Rust `monde_x64.dll` ( pont_rust/ ). Les ordres arrivent POUSSES par ExtensionCallback, en
// lots au format tableau simple : [n, [[ordre, args...], ...]]. Les rapports repartent par callExtension "envoyer".
//
// Ordres :
//   ["incarner", id, classe, camp, [x, y], rayon, cle]   un habitant devient un corps, dans un batiment du lieu
//   ["desincarner", id]                                    le corps disparait ; l habitant redevient une donnee
//   ["aller", id, [x, y], rayon, cle]                      le corps va au lieu ( batiment choisi par la cle )
//   ["temps", acceleration] ; ["date", [a, m, j, h, mi]]   l horloge du monde
// Rapports : ["pret", ...] au demarrage ; ["recu", n] par lot ; ["etat", ...] toutes les 2 s ; ["mort", id, ...].
// =====================================================================
MONDE_LOG = { diag_log ("MONDE|" + _this) };
MONDE_PORT = ["MONDE_PORT", 2350] call BIS_fnc_getParamValue;
MONDE_ACC = ["MONDE_ACCELERATION", 4] call BIS_fnc_getParamValue;
MONDE_CORPS = createHashMap;            // id de l habitant -> son corps
MONDE_CAMIONS = createHashMap;          // id de convoi -> [ vehicule, chauffeur, groupe, arrivee, depart_t, km, pos ]
MONDE_DEST = createHashMap;             // id -> destination courante
MONDE_LOTS = 0; MONDE_ERREURS = 0;

setDate [2035, 6, 15, 6, 0];
setTimeMultiplier MONDE_ACC;
0 setOvercast 0.1; 0 setFog 0; 0 setRain 0; forceWeatherChange;

MONDE_fnc_envoyer = {
    private _r = "monde" callExtension ["envoyer", [str _this]];
    if ((_r select 0) != "ok") then { MONDE_ERREURS = MONDE_ERREURS + 1 };
};

// un point de chute DETERMINISTE dans un lieu : le batiment n ( cle ) parmi ceux du rayon, trie par coordonnees
MONDE_fnc_point = {
    params ["_centre", "_rayon", "_cle"];
    private _c = [_centre select 0, _centre select 1, 0];
    private _b = (nearestObjects [_c, ["House"], _rayon]) select { count (_x buildingPos -1) > 0 };
    if (count _b == 0) exitWith { _c getPos [5 + (_cle mod 40), (_cle * 37) mod 360] };
    _b = [_b, [], { (round ((getPosATL _x) select 0)) * 100000 + round ((getPosATL _x) select 1) }, "ASCEND"] call BIS_fnc_sortBy;
    private _m = _b select (_cle mod (count _b));
    private _pts = _m buildingPos -1;
    _pts select (_cle mod (count _pts))
};

// un point SUR LA ROUTE le plus proche d un lieu : c est par la que roule un camion ( point 7 )
MONDE_fnc_pointRoute = {
    params ["_centre", "_rayon", ["_rang", 0]];
    private _c = [_centre select 0, _centre select 1, 0];
    private _r = _c nearRoads _rayon;
    if (count _r == 0) then { _r = _c nearRoads (_rayon * 4) };
    if (count _r == 0) exitWith { _c };
    private _m = [_r, [], { _c distance _x }, "ASCEND"] call BIS_fnc_sortBy;
    // le RANG evite que deux camions de la meme ville naissent au meme metre de route : mesure du 22/09, six camions
    // crees vivants puis detruits en une seconde, par paires, meme a trente metres d ecart.
    getPosATL (_m select (_rang mod (count _m)))
};

MONDE_fnc_executer = {
    params ["_o"];
    private _t = _o select 0;
    switch (_t) do {
        case "incarner": {
            _o params ["", "_id", "_classe", "_camp", "_centre", "_rayon", "_cle"];
            if (_id in MONDE_CORPS) exitWith {};                      // jamais deux corps pour un habitant
            private _p = [_centre, _rayon, _cle] call MONDE_fnc_point;
            private _u = objNull;
            if (_camp == "civ") then {
                _u = createAgent [_classe, _p, [], 0, "CAN_COLLIDE"];   // un civil : agent leger, sans groupe
            } else {
                private _g = createGroup [independent, true];
                _u = _g createUnit [_classe, _p, [], 0, "CAN_COLLIDE"];
                _g setBehaviour "SAFE"; _g setCombatMode "BLUE";
            };
            _u setPosATL _p;
            _u setVariable ["monde_id", _id];
            _u addEventHandler ["Killed", { params ["_u"]; ["mort", _u getVariable ["monde_id", -1], round (time * 100) / 100] call MONDE_fnc_envoyer }];
            MONDE_CORPS set [_id, _u];
        };
        case "desincarner": {
            private _id = _o select 1;
            private _u = MONDE_CORPS getOrDefault [_id, objNull];
            if (!isNull _u) then { private _g = group _u; deleteVehicle _u; if (!isNull _g && { count units _g == 0 }) then { deleteGroup _g } };
            MONDE_CORPS deleteAt _id; MONDE_DEST deleteAt _id;
        };
        case "aller": {
            _o params ["", "_id", "_centre", "_rayon", "_cle"];
            private _u = MONDE_CORPS getOrDefault [_id, objNull];
            if (isNull _u) exitWith {};
            private _p = [_centre, _rayon, _cle] call MONDE_fnc_point;
            // mesure du 22/09 ( essai_aller, 4 methodes, 3 corps chacune, 90 s ) : sur un AGENT, `moveTo` seul ne fait
            // rien du tout ( 0 m ) ; il faut d abord lui poser une destination. Un soldat en groupe obeit a `doMove`.
            if (isAgent teamMember _u) then { _u setDestination [_p, "LEADER PLANNED", true]; _u moveTo _p }
            else { _u doMove _p };
            MONDE_DEST set [_id, _p];
        };
        // --- essais de deplacement ( controle positif du 22/09 : l ordre « aller » ne bougeait aucun corps ) ---
        // methode 1 : agent + moveTo   2 : agent + setDestination + moveTo   3 : unite en groupe civil + doMove
        // methode 4 : unite en groupe civil + move du groupe
        case "essai_creer": {
            _o params ["", "_id", "_methode", "_centre", "_rayon", "_cle"];
            if (_id in MONDE_CORPS) exitWith {};
            private _p = [_centre, _rayon, _cle] call MONDE_fnc_point;
            private _u = objNull;
            if (_methode <= 2) then {
                _u = createAgent ["C_man_1", _p, [], 0, "CAN_COLLIDE"];
            } else {
                private _g = createGroup [civilian, true];
                _u = _g createUnit ["C_man_1", _p, [], 0, "CAN_COLLIDE"];
                _g setBehaviour "CARELESS"; _g setSpeedMode "LIMITED";
            };
            _u setPosATL _p;
            _u setVariable ["monde_id", _id];
            MONDE_CORPS set [_id, _u];
        };
        case "essai_aller": {
            _o params ["", "_id", "_methode", "_centre", "_rayon", "_cle"];
            private _u = MONDE_CORPS getOrDefault [_id, objNull];
            if (isNull _u) exitWith {};
            private _p = [_centre, _rayon, _cle] call MONDE_fnc_point;
            switch (_methode) do {
                case 1: { _u moveTo _p };
                case 2: { _u setDestination [_p, "LEADER PLANNED", true]; _u moveTo _p };
                case 3: { _u doMove _p };
                case 4: { (group _u) move _p };
            };
            MONDE_DEST set [_id, _p];
            (format ["essai|%1|methode|%2|agent|%3|simul|%4|anim|%5|de|%6|vers|%7|dist|%8", _id, _methode,
                isAgent teamMember _u, simulationEnabled _u, animationState _u, getPosATL _u, _p,
                round ((getPosATL _u) distance _p)]) call MONDE_LOG;
        };
        case "diag": {
            private _id = _o select 1;
            private _u = MONDE_CORPS getOrDefault [_id, objNull];
            if (isNull _u) exitWith { (format ["diag|%1|absent", _id]) call MONDE_LOG };
            (format ["diag|%1|pos|%2|dest|%3|reste|%4|vitesse|%5|anim|%6|pret|%7|comport|%8|agent|%9", _id, getPosATL _u,
                MONDE_DEST getOrDefault [_id, []], round ((getPosATL _u) distance (MONDE_DEST getOrDefault [_id, getPosATL _u])),
                speed _u, animationState _u, unitReady _u, behaviour _u, isAgent teamMember _u]) call MONDE_LOG;
        };
        // ["camion", id, [x,y] depart, [x,y] arrivee] : un convoi qui ROULE, par les routes d Altis ( point 7 )
        case "camion": {
            _o params ["", "_id", "_depart", "_arrivee"];
            if (_id in MONDE_CAMIONS) exitWith {};
            private _p0 = [_depart, 200, _id * 7] call MONDE_fnc_pointRoute;
            private _p1 = [_arrivee, 200, _id * 3] call MONDE_fnc_pointRoute;
            // 22/09 : le van « C_Van_01_box_F » vient d Apex et n existe pas sur ce serveur - les six premiers camions
            // sont nes morts, sans la moindre erreur. On prend un vehicule du jeu de base, et on le dit si ca rate.
            // rayon 30 m : deux camions partis de la meme ville naissaient au meme metre de route et s y detruisaient
            private _v = createVehicle ["C_Offroad_01_F", _p0, [], 10, "NONE"];
            if (isNull _v) exitWith { (format ["camion_impossible|%1|%2", _id, _p0]) call MONDE_LOG;
                ["camion", _id, "impossible", 0, 0] call MONDE_fnc_envoyer };
            private _g = createGroup [civilian, true];
            private _u = _g createUnit ["C_man_1", _p0, [], 0, "CAN_COLLIDE"];
            _u moveInDriver _v;
            _g setBehaviour "CARELESS"; _g setCombatMode "BLUE"; _g setSpeedMode "FULL";
            private _wp = _g addWaypoint [_p1, 0];
            _wp setWaypointType "MOVE"; _wp setWaypointBehaviour "CARELESS"; _wp setWaypointSpeed "FULL";
            _u doMove _p1;
            MONDE_CAMIONS set [_id, [_v, _u, _g, _p1, diag_tickTime, 0, getPosATL _v]];
            (format ["camion_cree|%1|type|%2|vivant|%3|pos|%4|vers|%5|chauffeur|%6|dans|%7", _id, typeOf _v, alive _v,
                getPosATL _v, _p1, alive _u, !isNull objectParent _u]) call MONDE_LOG;
        };
        case "rappeler_camion": {
            private _id = _o select 1;
            private _c = MONDE_CAMIONS getOrDefault [_id, []];
            if (count _c > 0) then { deleteVehicle (_c select 0); deleteVehicle (_c select 1); deleteGroup (_c select 2) };
            MONDE_CAMIONS deleteAt _id;
        };
        case "temps": { setTimeMultiplier (_o select 1) };
        case "date": { setDate (_o select 1) };
        default { (format ["ordre_inconnu|%1", _t]) call MONDE_LOG };
    };
};

addMissionEventHandler ["ExtensionCallback", {
    params ["_nom", "_fonction", "_donnees"];
    if (_nom != "monde") exitWith {};
    // arma-rs transmet une chaine SQF entre guillemets ( guillemets internes doubles ) : on la deballe d abord
    if ((_donnees select [0, 1]) == """") then { _donnees = (parseSimpleArray ("[" + _donnees + "]")) select 0 };
    private _lot = parseSimpleArray _donnees;
    if (count _lot < 2) exitWith { (format ["lot_illisible|%1", _donnees select [0, 120]]) call MONDE_LOG };
    { [_x] call MONDE_fnc_executer } forEach (_lot select 1);
    MONDE_LOTS = MONDE_LOTS + 1;
    ["recu", _lot select 0, count (_lot select 1), count MONDE_CORPS] call MONDE_fnc_envoyer;
}];

// les rapports : toutes les 2 s reelles, par paquets de 100 corps ( contexte non ordonnance : jamais en retard )
MONDE_T = diag_tickTime;
addMissionEventHandler ["EachFrame", {
    if (diag_tickTime - MONDE_T < 2) exitWith {};
    MONDE_T = diag_tickTime;
    private _corps = [];
    {
        private _p = getPosATL _y;
        _corps pushBack [_x, round (_p select 0), round (_p select 1), (if (alive _y) then {1} else {0}), round (speed _y)];
    } forEach MONDE_CORPS;
    // les camions : distance vraiment parcourue, arrivee, abandon
    {
        _y params ["_v", "_u", "_g", "_p1", "_t0", "_km", "_pos"];
        if (isNull _v || !alive _v) then {
            (format ["camion_perdu|%1|nul|%2|vivant|%3|chauffeur_nul|%4", _x, isNull _v, alive _v, isNull _u]) call MONDE_LOG;
            ["camion", _x, "perdu", round (_km / 100) / 10, round ((diag_tickTime - _t0) / 6) / 10] call MONDE_fnc_envoyer;
            MONDE_CAMIONS deleteAt _x;
        } else {
            private _p = getPosATL _v;
            _y set [5, _km + (_p distance _pos)];
            _y set [6, _p];
            if ((_p distance _p1) < 80) then {
                ["camion", _x, "arrive", round ((_y select 5) / 100) / 10, round ((diag_tickTime - _t0) / 6) / 10] call MONDE_fnc_envoyer;
                deleteVehicle _v; deleteVehicle _u; deleteGroup _g; MONDE_CAMIONS deleteAt _x;
            } else {
                if (diag_tickTime - _t0 > 1800) then {
                    ["camion", _x, "abandon", round ((_y select 5) / 100) / 10, round ((diag_tickTime - _t0) / 6) / 10] call MONDE_fnc_envoyer;
                    deleteVehicle _v; deleteVehicle _u; deleteGroup _g; MONDE_CAMIONS deleteAt _x;
                };
            };
        };
    } forEach MONDE_CAMIONS;
    private _n = count _corps; private _i = 0;
    ["etat", round (time * 100) / 100, date, round (dayTime * 10000) / 10000, round diag_fps, _n] call MONDE_fnc_envoyer;
    while { _i < _n } do {
        ["corps", _corps select [_i, 100]] call MONDE_fnc_envoyer;
        _i = _i + 100;
    };
}];

private _r = "monde" callExtension ["connecter", ["127.0.0.1", MONDE_PORT]];
(format ["connecter|%1|port|%2", _r, MONDE_PORT]) call MONDE_LOG;
[] spawn {
    waitUntil { sleep 1; (("monde" callExtension ["etat", []]) select 0) find "connecte=1" == 0 };
    ["pret", productVersion select 2, date, MONDE_ACC] call MONDE_fnc_envoyer;
    "pret" call MONDE_LOG;
    while { true } do { sleep 30; (format ["pont|%1|lots|%2|erreurs|%3|corps|%4", ("monde" callExtension ["etat", []]) select 0, MONDE_LOTS, MONDE_ERREURS, count MONDE_CORPS]) call MONDE_LOG };
};
