// alert_engine.sqf — MOTEUR D'ALERTE par secteur (HARMATTAN, REDFOR/CSAT)
// Valide sur Arma reel (occupation_react2.py) : contact -> detection t+32s -> alerte 0->3 -> QRF dispatchee + rapprochement.
// Chaque secteur tient un niveau HMT_ALERT_<SEC> {0 CALME .. 3 ENGAGE}. A lancer une fois ; tourne server-side.
if (!isServer) exitWith {};

HMT_SECTORS = ["NE","NO","SE","SO"];
{ missionNamespace setVariable ["HMT_ALERT_" + _x, 0]; missionNamespace setVariable ["HMT_QRF_SENT_" + _x, false]; } forEach HMT_SECTORS;
// poses par le laydown/runtime : HMT_QRF_<SEC> (group), HMT_HQ_<SEC> (pos)

HMT_fnc_sectorOf = {                       // quadrant autour du centre d'Altis
    params ["_pos"];
    private _ns = if ((_pos select 1) >= 13860) then {"N"} else {"S"};
    private _eo = if ((_pos select 0) >= 13860) then {"E"} else {"O"};
    _ns + _eo
};

[] spawn {
    while {true} do {
        {
            private _sec = _x;
            private _qrf = missionNamespace getVariable ["HMT_QRF_" + _sec, grpNull];
            private _al  = missionNamespace getVariable ["HMT_ALERT_" + _sec, 0];
            // contact = un BLUFOR connu (knowsAbout>1) d'un REDFOR, situe dans CE secteur
            private _contact = objNull;
            private _wests = allUnits select {(side _x == west) && (alive _x)};
            {
                private _e = _x;
                { if (((_e knowsAbout _x) > 1.0) && {([getPosATL _x] call HMT_fnc_sectorOf) == _sec}) exitWith { _contact = _x; }; } forEach _wests;
                if (!isNull _contact) exitWith {};
            } forEach (allUnits select {(side _x == east) && (alive _x)});
            if (!isNull _contact) then {
                _al = (_al + 1) min 3;                                  // escalade
                if (!(missionNamespace getVariable ["HMT_QRF_SENT_" + _sec, false]) && {!isNull _qrf}) then {
                    missionNamespace setVariable ["HMT_QRF_SENT_" + _sec, true];
                    { _x doMove (getPosATL _contact) } forEach (units _qrf);
                    _qrf setBehaviour "COMBAT"; _qrf setCombatMode "RED";
                    diag_log format ["HARMATTAN_QRF %1 DISPATCH vers %2", _sec, mapGridPosition (getPosATL _contact)];
                };
            } else {
                _al = (_al - 0.4) max 0;                                // de-escalade
                if (_al <= 0) then { missionNamespace setVariable ["HMT_QRF_SENT_" + _sec, false]; };   // re-arme la QRF
            };
            missionNamespace setVariable ["HMT_ALERT_" + _sec, _al];
            diag_log format ["HARMATTAN_ALERT %1 niveau=%2 contact=%3", _sec, round(_al*10)/10, !isNull _contact];
        } forEach HMT_SECTORS;
        sleep 5;
    };
};
diag_log "HARMATTAN_ALERT_ENGINE demarre (4 secteurs)";
