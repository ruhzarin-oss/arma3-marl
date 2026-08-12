if (!isNil "HMT_ZEUS_ACTIF") exitWith { diag_log "Q_ZEUS deja actif"; };
HMT_ZEUS_ACTIF = true;
diag_log "Q_ZEUS veilleur arme";

[] spawn {
    while {true} do {
        {
            private _j = _x;
            private _log = getAssignedCuratorLogic _j;
            if (isNull _log) then {
                private _c = (createGroup sideLogic) createUnit ["ModuleCurator_F", [0,0,0], [], 0, "NONE"];
                _c setVariable ["showNotification", false];
                _c setVariable ["Addons", 3];
                _j assignCurator _c;
                diag_log format ["Q_ZEUS attribue a %1", name _j];
                ("HMT_ZEUS attribue a " + (name _j)) call HMT_OUT;
            } else {
                _log addCuratorEditableObjects [allUnits + vehicles + allDeadMen, true];
            };
        } forEach (allPlayers - entities "HeadlessClient_F");
        sleep 5;
    };
};
