// caserne_sud.sqf — CASERNE BLUEFOR / OTAN (sud de Stratis) + arsenal ACE complet.
// Base avancee de la faction NATO (west, RHS USAF) face au pays russe (east).
// Durable (chargee par init.sqf apres fob_network) ET injectable live. Idempotent.
if (!isServer) exitWith {};

// --- nettoyage si deja construite (rejouable sans doublon) ---
if (!isNil "HMT_CAS_OBJ") then { { deleteVehicle _x } forEach HMT_CAS_OBJ; };
if (!isNil "HMT_CAS_GRP") then { { { deleteVehicle _x } forEach (units _x); deleteGroup _x; } forEach HMT_CAS_GRP; };
if (!isNil "HMT_CASERNE_MK") then { deleteMarker "HMT_CASERNE_MK"; };
HMT_CAS_OBJ = []; HMT_CAS_GRP = []; HMT_CAS_MEN = []; HMT_CAS_ARSENAL = objNull;

// --- emplacement : sud de l'ile, snappe sur terre (HMT_LAND vient de fob_network) ---
private _o = [2300, 2000, 0];   // sud de Stratis, point le plus plat trouve (planeite ~2m, anneau sec)
if (!isNil "HMT_LAND") then { _o = [_o] call HMT_LAND; };
HMT_CAS_POS = _o;
private _cx = _o select 0; private _cy = _o select 1;

private _mk = {
    params ["_cls","_dx","_dy","_dir"];
    private _p = [_cx + _dx, _cy + _dy, 0];
    private _obj = createVehicle [_cls, _p, [], 0, "CAN_COLLIDE"];
    _obj setDir _dir; _obj setPosATL _p; _obj allowDamage false;
    _obj enableSimulation true; _obj enableDynamicSimulation false;
    HMT_CAS_OBJ pushBack _obj; _obj
};

// --- enceinte HBarrier (rectangle ~52 x 40 m), porte au nord (face au pays) ---
private _hw = 26; private _hh = 20;
private _wx = -_hw;
while { _wx <= _hw } do {
    ["Land_HBarrierBig_F", _wx, -_hh, 0] call _mk;                       // mur sud (plein)
    if (abs _wx > 7) then { ["Land_HBarrierBig_F", _wx, _hh, 0] call _mk; };  // mur nord (porte au centre)
    _wx = _wx + 6;
};
private _wy = -_hh + 6;
while { _wy <= _hh - 6 } do {
    ["Land_HBarrierBig_F", -_hw, _wy, 90] call _mk;                      // mur ouest
    ["Land_HBarrierBig_F",  _hw, _wy, 90] call _mk;                      // mur est
    _wy = _wy + 6;
};

// --- batiments : QG, dortoirs, tours de guet ---
["Land_Cargo_HQ_V3_F",     0, -2, 0]   call _mk;                        // poste de commandement
["Land_Cargo_House_V3_F", -14,  7, 90]  call _mk;                       // dortoir 1
["Land_Cargo_House_V3_F", -14, -8, 90]  call _mk;                       // dortoir 2
["Land_Cargo_House_V3_F",  14,  7, 270] call _mk;                       // dortoir 3
["Land_Cargo_Tower_V3_F",  (-_hw+3),  (_hh-3), 0] call _mk;             // tour coin NO
["Land_Cargo_Tower_V3_F",  (_hw-3),   (_hh-3), 0] call _mk;             // tour coin NE
["Land_Cargo_Patrol_V3_F", (-_hw+3), (-_hh+3), 0] call _mk;            // guet coin SO
["Land_Cargo_Patrol_V3_F", (_hw-3),  (-_hh+3), 0] call _mk;            // guet coin SE

// --- point d'appui devant la porte + eclairage ---
["Land_BagBunker_Large_F", 0, (_hh+4), 0] call _mk;                     // bunker face au nord (l'ennemi)
["Land_PortableLight_double_F", -6, 0, 0] call _mk;
["Land_PortableLight_double_F",  6, 0, 0] call _mk;

// --- drapeau OTAN au centre ---
private _flag = ["Flag_NATO_F", 3, -6, 0] call _mk;

// --- helipad + parc vehicules (BLUFOR) au sud, hors enceinte ---
["Land_HelipadSquare_F", 0, (-_hh-24), 0] call _mk;
["B_Heli_Light_01_F",    0, (-_hh-24), 0] call _mk;                     // helo leger sur le pad
["B_MRAP_01_hmg_F",    -12, (-_hh-10), 0] call _mk;                     // MRAP HMG
["B_MRAP_01_hmg_F",     12, (-_hh-10), 0] call _mk;
["B_Truck_01_transport_F", 20, (-_hh-10), 90] call _mk;                // camion transport

// --- ARSENAL ACE COMPLET (tout l'arsenal OTAN), BIEN EN EVIDENCE : a l'air libre, juste devant le spawn, eclaire + marqueur ---
private _ap1 = [_cx - 4, _cy + 4, 0];   // caisse equipement (gauche du spawn)
private _ap2 = [_cx + 4, _cy + 4, 0];   // caisse armes (droite du spawn)
private _ars = "Box_NATO_Equip_F" createVehicle _ap1;
_ars setPosATL _ap1; _ars allowDamage false; _ars enableSimulation true; _ars enableDynamicSimulation false;
if (!isNil "ace_arsenal_fnc_initBox") then { [_ars, true] call ace_arsenal_fnc_initBox; } else { ["AmmoboxInit",[_ars,true]] call BIS_fnc_arsenal; };
HMT_CAS_OBJ pushBack _ars; HMT_CAS_ARSENAL = _ars;
private _ars2 = "Box_NATO_Wps_F" createVehicle _ap2;
_ars2 setPosATL _ap2; _ars2 allowDamage false; _ars2 enableSimulation true; _ars2 enableDynamicSimulation false;
if (!isNil "ace_arsenal_fnc_initBox") then { [_ars2, true] call ace_arsenal_fnc_initBox; } else { ["AmmoboxInit",[_ars2,true]] call BIS_fnc_arsenal; };
HMT_CAS_OBJ pushBack _ars2;
// mise en evidence : lampe entre les 2 caisses + marqueur carte ARSENAL
private _lamp = "Land_PortableLight_double_F" createVehicle [_cx, _cy + 3, 0];
_lamp setPosATL [_cx, _cy + 3, 0]; _lamp allowDamage false; HMT_CAS_OBJ pushBack _lamp;
deleteMarker "HMT_ARSENAL_MK";
createMarker ["HMT_ARSENAL_MK", [_cx, _cy + 4, 0]];
"HMT_ARSENAL_MK" setMarkerType "loc_Ammo"; "HMT_ARSENAL_MK" setMarkerColor "ColorWEST"; "HMT_ARSENAL_MK" setMarkerText "ARSENAL"; "HMT_ARSENAL_MK" setMarkerSize [0.8, 0.8];

// --- AUCUNE garnison (choix Younes) : caserne vide, pretes a etre peuplee plus tard ---
//   (le nettoyage en tete supprime toute garnison eventuellement construite avant)

// --- marqueur carte (installation OTAN) ---
createMarker ["HMT_CASERNE_MK", _o];
"HMT_CASERNE_MK" setMarkerType "b_installation";
"HMT_CASERNE_MK" setMarkerColor "ColorWEST";
"HMT_CASERNE_MK" setMarkerText "CASERNE OTAN (SUD)";

// point de respawn BLUFOR = la caserne (dans l'enceinte, pres de l'arsenal)
deleteMarker "respawn_west";
createMarker ["respawn_west", [_cx, _cy + 6, 0]];
"respawn_west" setMarkerType "Empty";
HMT_CAS_SPAWN = [_cx, _cy + 6, 0];

diag_log format ["HARMATTAN_CASERNE OTAN sud @ %1 | objs=%2 hommes=%3 arsenal=%4", _o, count HMT_CAS_OBJ, count HMT_CAS_MEN, !isNull HMT_CAS_ARSENAL];
if (!isNil "HMT_EMIT") then { (format ["HARMATTAN_CASERNE OTAN sud @ %1 objs=%2 hommes=%3", _o, count HMT_CAS_OBJ, count HMT_CAS_MEN]) call HMT_EMIT; };
