// spawn_fix.sqf — sort tout joueur de son batiment au spawn (terrain degage), une fois par apparition.
HMT_OUTFN = {
    params ["_u"];
    private _c = getPosATL _u;
    private _dest = [_c, 3, 200, 13, 0, 0.5, 0] call BIS_fnc_findSafePos;
    if (count _dest < 2 || { (_dest distance2D _c) > 400 }) then { _dest = _c; };
    _u setPosATL [_dest select 0, _dest select 1, 0.4];
    _u setPos [_dest select 0, _dest select 1, 0];
    diag_log format ["HARMATTAN_SPAWNOUT %1 -> [%2,%3]", name _u, round (_dest select 0), round (_dest select 1)];
};
// 1) sortir le(s) joueur(s) deja la, maintenant
{ if (isPlayer _x) then { [_x] call HMT_OUTFN; _x setVariable ["HMT_OUTDONE", true]; }; } forEach allUnits;
// 2) boucle : sortir tout nouveau joueur UNE fois (au spawn)
if (!isNil "HMT_SPAWNFIX_H") then { terminate HMT_SPAWNFIX_H; HMT_SPAWNFIX_H = nil; };
HMT_SPAWNFIX_H = [] spawn {
    while { true } do {
        {
            if (isPlayer _x && { alive _x } && { !(_x getVariable ["HMT_OUTDONE", false]) }) then {
                [_x] call HMT_OUTFN; _x setVariable ["HMT_OUTDONE", true];
            };
        } forEach allUnits;
        sleep 2;
    };
};
diag_log "HARMATTAN_SPAWNFIX ON";
