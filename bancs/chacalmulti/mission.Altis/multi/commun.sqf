// =====================================================================
// CHACAL MULTI - LE COMMUN. Ce que les cellules partagent : l'attribution des unites a leur cellule, la lecture
// des parametres, et la distance aux autres cellules. Tout le reste est a la cellule ( c<k>\*.sqf ).
//
// Journal : toute ligne porte `M|<cellule>|`. La cellule 0 est l'episode lui-meme ( charge, sonde, croisements ).
// =====================================================================
MULTI_LOG = { diag_log ("M|0|MULTI|" + _this) };
MULTI_VERSION = 1;

// --- parametre d'une cellule : la surcharge de la cellule si le job en a pose une, sinon la valeur commune ---
// Appele par 00_socle de chaque cellule a la place de BIS_fnc_getParamValue, avec le nom renomme : "MC3_GRAINE".
MULTI_fnc_param = {
    params ["_n", "_d"];
    private _i = _n find "_";
    private _k = _n select [2, _i - 2];
    private _x = _n select [_i + 1];
    private _nc = format ["MULTI_C%1_%2", _k, _x];
    private _v = -999999;
    if (isClass (missionConfigFile >> "Params" >> _nc)) then { _v = [_nc, -999999] call BIS_fnc_getParamValue };
    if (_v != -999999) exitWith { _v };
    [("CHACAL_" + _x), _d] call BIS_fnc_getParamValue
};

// --- l'appartenance : un groupe cree par la cellule k porte k ; une unite prend celle de son groupe, et la garde
// ( un mort quitte son groupe ; un vehicule prend celle de son equipage, posee par le recenseur de sa cellule ) ---
MULTI_fnc_groupe = {
    params ["_camp", "_k"];
    private _g = createGroup _camp;
    _g setVariable ["multi_c", _k];
    _g
};
MULTI_fnc_cellule = {
    private _c = _this getVariable ["multi_c", -1];
    if (_c < 0) then {
        _c = (group _this) getVariable ["multi_c", -1];
        if (_c >= 0) then { _this setVariable ["multi_c", _c] };
    };
    _c
};

// --- les emprises : les points de chaque cellule, echantillonnes le long de ses trajets ---
MULTI_EMPRISES = [];   // [k, [points]]
MULTI_fnc_segment = {
    params ["_a", "_b"];
    private _n = ((ceil ((_a distance2D _b) / 250)) max 1);
    private _r = [];
    for "_i" from 0 to _n do {
        _r pushBack [(_a select 0) + (((_b select 0) - (_a select 0)) * _i / _n), (_a select 1) + (((_b select 1) - (_a select 1)) * _i / _n), 0];
    };
    _r
};
MULTI_fnc_pointsEmprise = {
    params ["_k"];
    private _v = { missionNamespace getVariable [format ["MC%1_%2", _k, _this], []] };
    private _pts = [];
    _pts append (["LZ" call _v, "ROUTE" call _v] call MULTI_fnc_segment);
    _pts append (["ROUTE" call _v, "OP" call _v] call MULTI_fnc_segment);
    _pts append (["OP" call _v, "SITE" call _v] call MULTI_fnc_segment);
    _pts append (["SITE" call _v, "RALLY" call _v] call MULTI_fnc_segment);
    { if (count _x > 1) then { _pts pushBack _x } } forEach ["QRF_BASE" call _v, "ROUTE_A" call _v, "ROUTE_B" call _v, "PZ" call _v];
    _pts
};
MULTI_fnc_enregistrerEmprise = {
    params ["_k"];
    MULTI_EMPRISES pushBack [_k, [_k] call MULTI_fnc_pointsEmprise];
};
// vrai si _p est a MULTI_ESPACEMENT au moins de toute emprise d'une AUTRE cellule que _k ( _k = 0 : de toutes )
MULTI_fnc_loin = {
    params ["_p", "_k"];
    private _ok = true;
    {
        _x params ["_kk", "_pts"];
        if (_kk != _k) then { { if ((_x distance2D _p) < MULTI_ESPACEMENT) exitWith { _ok = false } } forEach _pts };
        if (!_ok) exitWith {};
    } forEach MULTI_EMPRISES;
    _ok
};
MULTI_fnc_ecartMin = {
    params ["_a", "_b"];
    private _m = 1e9;
    { private _p = _x; { _m = _m min (_p distance2D _x) } forEach _b } forEach _a;
    _m
};

// --- monter une cellule : le meme ordre que l'initServer du banc seul, les memes sorties VOID ---
MULTI_fnc_monter = {
    params ["_k"];
    private _v = { missionNamespace getVariable [format ["MC%1_%2", _k, _this], ""] };
    private _f = { call compile preprocessFileLineNumbers format ["c%1\%2.sqf", _k, _this] };
    private _void = {
        (format ["CHACAL|FINI|VOID|%1|graine|%2", "CAUSE" call _v, "GRAINE" call _v]) call ("LOG" call _v);
        false
    };
    "00_socle" call _f;
    "10_monde" call _f;
    if (("ISSUE" call _v) == "VOID") exitWith { call _void };
    // ! LE MONDE TIRE DOIT ETRE CELUI DU BANC SEUL, ET LOIN DES AUTRES ( service du 22/09, 14 h 12 ) : 2 cellules sur 25
    // ont tire un autre monde que leur graine ( sites a 11 et 13 km de la table ), et l une est tombee a 117 m d une autre
    // cellule. La cellule est annulee AVANT de creer la moindre unite : rien ne peut plus toucher ses voisines.
    private _sx = [format ["MULTI_C%1_SITE_X", _k], -999999] call BIS_fnc_getParamValue;
    private _sy = [format ["MULTI_C%1_SITE_Y", _k], -999999] call BIS_fnc_getParamValue;
    private _site = "SITE" call _v;
    if ((_sx != -999999) && { (_site distance2D [_sx, _sy, 0]) > 5 }) exitWith {
        missionNamespace setVariable [format ["MC%1_ISSUE", _k], "VOID"];
        missionNamespace setVariable [format ["MC%1_CAUSE", _k], "MONDE_NON_CONFORME"];
        (format ["CHACAL|AVERT|monde_non_conforme|site|%1|attendu|%2|ecart|%3", _site, [_sx, _sy], round (_site distance2D [_sx, _sy, 0])]) call ("LOG" call _v);
        call _void
    };
    private _ecart = 1e9;
    { _ecart = _ecart min ([[_k] call MULTI_fnc_pointsEmprise, _x select 1] call MULTI_fnc_ecartMin) } forEach MULTI_EMPRISES;
    if (_ecart < MULTI_ESPACEMENT_MIN) exitWith {
        missionNamespace setVariable [format ["MC%1_ISSUE", _k], "VOID"];
        missionNamespace setVariable [format ["MC%1_CAUSE", _k], "CELLULE_TROP_PROCHE"];
        (format ["CHACAL|AVERT|cellule_trop_proche|metres|%1|minimum|%2", round _ecart, MULTI_ESPACEMENT_MIN]) call ("LOG" call _v);
        call _void
    };
    "20_decor" call _f;
    if (("ISSUE" call _v) == "VOID") exitWith { call _void };
    "30_opfor" call _f;
    "35_menaces" call _f;
    "40_blufor" call _f;
    if (("ISSUE" call _v) == "VOID") exitWith { call _void };
    "45_oracle" call _f;
    "46_controles_oracle" call _f;
    "50_capture" call _f;
    "70_verdict" call _f;
    "60_phases" call _f;
    (format ["CHACAL|OK|monte|%1|est|%2|ouest|%3|graine|%4|echelle|%5",
        "VERSION" call _v, count ("EST_SITE" call _v), count ("FS" call _v),
        "GRAINE" call _v, "ECHELLE" call _v]) call ("LOG" call _v);
    true
};
