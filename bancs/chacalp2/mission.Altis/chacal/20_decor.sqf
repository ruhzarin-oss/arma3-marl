// =====================================================================
// CHACAL - LE SITE DE GUERRE ELECTRONIQUE.
//
// Trois objets sont l objectif et rien d autre : deux antennes et le poste de
// commandement. Ils sont poses AVANT les hommes, parce que la garnison se
// garnit dans les batiments : l ordre compte.
//
// ! Tout le site est en POLAIRE RELATIVE a CHACAL_AZ. Le premier jet batissait
// l enceinte en gisement ABSOLU pendant que les batiments tournaient, et
// l assaut visait une ouverture exprimee en relatif : des que l axe n etait ni
// 0 ni 180, il chargeait un mur.
//
// ! " Deux ouvertures " etait faux. Vingt segments sur un perimetre de 289 m
// font un pas de 14,45 m ; un HBarrier fait 9 m ; il restait une vingtaine de
// breches de 5 m. On MESURE donc le segment et on en pose assez pour fermer.
// =====================================================================

private _c = CHACAL_SITE;
CHACAL_AZ = _c getDir CHACAL_OP;        // l orientation vient de la geometrie tiree
CHACAL_RAYON = 46;

private _temoin = createVehicle ["Land_HBarrier_Big_F", [(_c select 0) + 400, (_c select 1) + 400, 0], [], 0, "CAN_COLLIDE"];
private _bb = boundingBoxReal _temoin;
private _lg = ((_bb select 1) select 0) - ((_bb select 0) select 0);
private _lg2 = ((_bb select 1) select 1) - ((_bb select 0) select 1);
if (_lg2 > _lg) then { _lg = _lg2 };
deleteVehicle _temoin;
if (_lg < 2) then { _lg = 8.5 };

private _perim = 2 * pi * CHACAL_RAYON;
private _n = ceil (_perim / (_lg * 0.92));          // 8 % de recouvrement : on ferme vraiment
private _pas = 360 / _n;
private _jeu = (_perim / _n) - _lg;

// Les deux portes, en gisement RELATIF. La MEME variable sert a batir et a viser.
CHACAL_PORTES = [99, 279];
private _large = 2;
private _iPortes = CHACAL_PORTES apply { round (_x / _pas) };
private _sautes = [];
{ private _i0 = _x; for "_k" from 0 to (_large - 1) do { _sautes pushBackUnique ((_i0 + _k) % _n) }; } forEach _iPortes;

for "_i" from 0 to (_n - 1) do {
    if (!(_i in _sautes)) then {
        ["Land_HBarrier_Big_F", _c, CHACAL_RAYON, _i * _pas, (_i * _pas) + 90] call CHACAL_fnc_poseP;
    };
};
// ! Les ouvertures sont des POSITIONS, pas des azimuts : la phase 4 leur
// applique `distance2D` pour compter les sentinelles autour, et le choix de
// l ouverture la moins gardee echouait a chaque episode, en silence.
CHACAL_OUV_AZ = _iPortes apply { ((_x + ((_large - 1) / 2)) * _pas) };
CHACAL_OUVERTURES = CHACAL_OUV_AZ apply { private _a = _x; _c getPos [CHACAL_RAYON, CHACAL_AZ + _a] };

CHACAL_PC       = ["Land_Cargo_HQ_V1_F",     _c,  0,  0,   0] call CHACAL_fnc_poseP;
["Land_Cargo_House_V1_F", _c, 30, 208, 0] call CHACAL_fnc_poseP;
["Land_Cargo_House_V1_F", _c, 31,  40, 0] call CHACAL_fnc_poseP;
CHACAL_TOUR     = ["Land_Cargo_Patrol_V1_F", _c, 31, 15, 160] call CHACAL_fnc_poseP;
["Land_CampingTable_F", _c, 10, 143, 0] call CHACAL_fnc_poseP;
CHACAL_PORTABLE = ["Land_Laptop_unfolded_F", _c, 10.6, 143, 0] call CHACAL_fnc_poseP;

CHACAL_ANT = [];
private _a1 = ["Land_TTowerBig_1_F", _c, 41, 227, 0] call CHACAL_fnc_poseP;
if (!isNull _a1) then { CHACAL_ANT pushBack _a1 };
private _a2 = ["Land_Communication_F", _c, 41, 51, 0] call CHACAL_fnc_poseP;
if (isNull _a2) then { _a2 = ["Land_TTowerBig_2_F", _c, 41, 51, 0] call CHACAL_fnc_poseP };
if (!isNull _a2) then { CHACAL_ANT pushBack _a2 };
CHACAL_RADAR  = ["Land_Radar_Small_F", _c, 34, 353, 0] call CHACAL_fnc_poseP;
CHACAL_GROUPE = ["Land_Portable_generator_F", _c, 13, 297, 0] call CHACAL_fnc_poseP;

CHACAL_LAMPES = [];
{
    private _l = ["Land_LampHalogen_F", _c, _x select 0, _x select 1, _x select 2] call CHACAL_fnc_poseP;
    if (!isNull _l) then { CHACAL_LAMPES pushBack _l };
} forEach [[21,41,210],[19,251,60],[33,115,300],[35,347,120],[36,180,0]];

CHACAL_BUNKERS = [];
{
    private _b = ["Land_BagBunker_Small_F", _c, _x select 0, _x select 1, _x select 2] call CHACAL_fnc_poseP;
    if (!isNull _b) then { CHACAL_BUNKERS pushBack _b };
} forEach [[43,77,95],[45,342,350],[46,157,175],[45,249,265]];

["Land_Cargo_House_V1_F", CHACAL_QRF_BASE, 0, 0, 360 call CHACAL_fnc_al] call CHACAL_fnc_pose;
["Land_LampHalogen_F", CHACAL_QRF_BASE, 8, 6, 180] call CHACAL_fnc_pose;

CHACAL_OBJETS = (CHACAL_ANT + [CHACAL_PC]) select { !isNull _x };

if (count CHACAL_MANQUANTES > 0) then {
    (format ["CHACAL|AVERT|classes_absentes|%1", CHACAL_MANQUANTES]) call CHACAL_LOG;
};
if (count CHACAL_OBJETS < 3) then {
    CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "OBJECTIFS_INCOMPLETS";
    (format ["CHACAL|VOID|objectifs|%1", count CHACAL_OBJETS]) call CHACAL_LOG;
};

(format ["CHACAL|OK|enceinte|segments|%1|poses|%2|longueur|%3|pas|%4|jeu|%5|portes|%6|az|%7",
    _n, _n - (count _sautes), round (_lg * 100) / 100, round (_pas * 100) / 100,
    round (_jeu * 100) / 100, CHACAL_OUV_AZ, round CHACAL_AZ]) call CHACAL_LOG;
(format ["CHACAL|OK|decor|objets|%1|antennes|%2|lampes|%3|props|%4",
    count CHACAL_OBJETS, count CHACAL_ANT, count CHACAL_LAMPES, count CHACAL_PROPS]) call CHACAL_LOG;
