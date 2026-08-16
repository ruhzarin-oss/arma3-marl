// officer_sit.sqf — SITREP en FONCTION (evite l'echec-compile du gros inline sur le pont fichier).
// Charge une fois ; ensuite `call HMT_SITREP` (inline court, robuste) emet HARMATTAN_SIT.
if (!isServer) exitWith {};
HMT_SITREP = {
    private _east = allUnits select {side _x == east && alive _x};
    private _wk = allUnits select {side _x != east && side _x != civilian && alive _x && (east knowsAbout _x > 1)};
    private _s = "";
    {
        private _c = [_x select 0, _x select 1, 0];
        private _g = { private _u = _x; (_u distance _c) < 250 } count _east;
        private _k = { private _u = _x; (_u distance _c) < 350 } count _wk;
        _s = _s + format ["%1,%2;", _g, _k];
    } forEach HMT_FOB_ANCHORS;
    private _ti = { !isNull _x && alive _x } count HMT_TARGET;
    diag_log format ["HARMATTAN_SIT %1#%2#%3#%4#%5", _s, _ti, count HMT_TARGET, dayTime, count _east];
    if (!isNil "HMT_EMIT") then { (format ["HARMATTAN_SIT %1#%2#%3#%4#%5", _s, _ti, count HMT_TARGET, dayTime, count _east]) call HMT_EMIT; };
};
diag_log "HARMATTAN_SITREP_FN charge";
