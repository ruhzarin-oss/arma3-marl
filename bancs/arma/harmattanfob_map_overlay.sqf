// map_overlay.sqf v3 — overlay carte FIXE et PROPRE (update en place + purge orphelins + stoppable).
if (!isNil "HMT_OVL2_ON") exitWith { diag_log "HARMATTAN_OVERLAY2 deja ON"; };
HMT_OVL2_ON = true;
if (isNil "HMT_OVP_N") then { HMT_OVP_N = 0; };

HMT_OVL_FOBS = [
    ["Mike26",4279,3856],["AirBase",2050,5700],["Maxwell",3253,2984],["Kamino",6544,4863],["Rogain",4886,5948],["AgiaMarina",2915,6165],
    ["Tempest",1942,3557],["OldOutpost",4319,4398],["LZBaldy",4604,5284],["MilRange",3338,5744],["AgiosIoannis",3027,2184],["Tsoukalia",4206,2715],
    ["Girna",1935,2723],["KaminoFR",6402,5427],["LZConnor",2979,1860],["AgiosCephas",2719,1712],["Strogos",2024,1790],["Keiros",6157,4349],
    ["Limeri",5440,3687],["Nisi",1784,4134],["Kyfi",1790,3512],["MarinaBay",2648,5990],["Tsoukala",4241,2498],["KaminoCoast",5691,6124],["GirnaBay",1845,2656]
];

// --- statiques : FOB + cibles (creees une fois, fixes) ---
{
    private _n = format ["ovl_fob_%1", _forEachIndex];
    if (markerType _n == "") then {
        private _m = createMarker [_n, [_x select 1, _x select 2]];
        _m setMarkerType "loc_Bunker"; _m setMarkerColor "ColorBlue"; _m setMarkerText (_x select 0); _m setMarkerSize [0.7, 0.7];
    };
} forEach HMT_OVL_FOBS;
if (!isNil "HMT_TARGETS") then {
    {
        private _t = _x select 1; private _n = format ["ovl_tgt_%1", _forEachIndex];
        if (!isNull _t && {markerType _n == ""}) then {
            private _m = createMarker [_n, getPosATL _t];
            _m setMarkerType "mil_objective"; _m setMarkerColor "ColorOrange"; _m setMarkerText (_x select 0);
        };
    } forEach HMT_TARGETS;
};

// --- boucle FIXE (stoppable via HMT_OVL_HANDLE) ---
HMT_OVL_HANDLE = [] spawn {
    while { true } do {
        // purge des orphelins : tout marker ovp_ dont l'unite n'est plus vivante
        private _valid = (allUnits select { alive _x }) apply { _x getVariable ["HMT_OVP", ""] };
        { if (!(_x in _valid)) then { deleteMarker _x }; } forEach (allMapMarkers select { (_x find "ovp_") == 0 });
        // update EN PLACE : un marker persistant par unite vivante
        {
            private _u = _x;
            private _mk = _u getVariable ["HMT_OVP", ""];
            if (alive _u) then {
                if (_mk == "" || {markerType _mk == ""}) then {
                    _mk = format ["ovp_%1", HMT_OVP_N]; HMT_OVP_N = HMT_OVP_N + 1;
                    createMarker [_mk, getPosATL _u];
                    _u setVariable ["HMT_OVP", _mk];
                };
                _mk setMarkerPos (getPosATL _u);
                private _s = side _u; private _col = "ColorWhite"; private _typ = "hd_dot";
                if (_s == east) then { _col = "ColorBlue"; if (_u getVariable ["HMT_SHELL", false]) then { _col = "ColorYellow"; }; };
                if (_s == civilian) then { _col = "ColorGreen"; };
                if (_s == west || {_s == resistance}) then { _col = "ColorRed"; _typ = "mil_dot"; };
                _mk setMarkerType _typ; _mk setMarkerColor _col; _mk setMarkerSize [0.5, 0.5];
            };
        } forEach allUnits;
        sleep 1.5;
    };
};
diag_log "HARMATTAN_OVERLAY3 fixe+propre ON";
