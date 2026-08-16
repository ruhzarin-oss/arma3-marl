// player_marker.sqf — marqueur perso "MOI" (rose) qui suit le joueur sur la carte.
if (!isNil "HMT_MOI_H") then { terminate HMT_MOI_H; HMT_MOI_H = nil; };
deleteMarker "ovl_moi";
createMarker ["ovl_moi", [2000, 2000]];
"ovl_moi" setMarkerType "hd_flag";
"ovl_moi" setMarkerColor "ColorPink";
"ovl_moi" setMarkerText "MOI";
"ovl_moi" setMarkerSize [1.5, 1.5];
HMT_MOI_H = [] spawn {
    while {true} do {
        private _pl = allUnits select { isPlayer _x };
        if (count _pl > 0) then { "ovl_moi" setMarkerPos (getPosATL (_pl select 0)); };
        sleep 0.5;
    };
};
diag_log "HARMATTAN_MOI marqueur joueur ON";
