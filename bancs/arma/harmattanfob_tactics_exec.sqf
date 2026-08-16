// tactics_exec.sqf — EXECUTEURS des 5 tactiques de l'orchestration (0=TIR 1=GRENADE 2=FLANC 3=FUMI 4=SUPPR).
// Traduit la sortie du .pt en action Arma REELLE + VISIBLE. Dispatch par netId (depuis HMT_ORCH_SNAP).
if (!isServer) exitWith {};

// point de flanc : ~55 m sur le cote de l'ennemi (vu de l'unite)
HMT_FLANK_PT = {
    params ["_u", "_e"];
    private _d = (_u getDir _e) + (selectRandom [65, -65]);
    (getPosATL _e) getPos [55, _d]
};

// l'unite a-t-elle un chargeur dont l'ammo herite de _kind (GrenadeHand / SmokeShell) ?
HMT_HAS_MAG = {
    params ["_u", "_kind"];
    ({ (getText (configFile >> "CfgMagazines" >> _x >> "ammo")) isKindOf [_kind, configFile >> "CfgAmmo"] } count (magazines _u)) > 0
};

// applique la tactique _tac a l'unite _u ; renvoie une description de l'action
HMT_TAC_EXEC = {
    params ["_u", "_tac"];
    if (!alive _u) exitWith { "mort" };
    private _e = _u findNearestEnemy _u;
    if (isNull _e) exitWith { "pas_d_ennemi" };
    // COMPOSITION : on n'ecrase PAS le reflexe de l'agent, on FOCALISE + on AJOUTE ce qu'il ne fait pas seul.
    private _act = "";
    switch (_tac) do {
        case 0: {                                                   // TIR VISE : focalise le tir du reflexe sur la cible choisie
            _u doTarget _e; _u doFire _e;
            _act = "TIR";
        };
        case 1: {                                                   // GRENADE (frag dispo + a portee) sinon TIR
            if ((_u distance _e < 45) && {[_u, "GrenadeHand"] call HMT_HAS_MAG}) then {
                private _start = _u modelToWorld [0, 0.6, 1.5];
                private _g = "GrenadeHand" createVehicle _start;
                _g setPosATL _start;
                private _dir = (getPosATL _e) vectorDiff (getPosATL _u);
                _g setVelocity ((vectorNormalized _dir) vectorMultiply 18 vectorAdd [0,0,7]);
                _act = "GRENADE";
            } else { _u doTarget _e; _u doFire _e; _act = "GRENADE>TIR"; };
        };
        case 2: {                                                   // FLANC : suggere une route de flanc (le reflexe garde son couvert en chemin)
            private _fp = [_u, _e] call HMT_FLANK_PT;
            _u doMove _fp;
            _act = "FLANC";
        };
        case 3: {                                                   // FUMIGENE (si dispo)
            if ([_u, "SmokeShell"] call HMT_HAS_MAG) then {
                private _sp = (getPosATL _u) getPos [14, _u getDir _e];
                "SmokeShell" createVehicle _sp;
                _act = "FUMI";
            } else { _u doTarget _e; _u doFire _e; _act = "FUMI>TIR"; };
        };
        case 4: {                                                   // SUPPRESSION
            _u doSuppressiveFire _e; _u setUnitPos "AUTO";
            _act = "SUPPR";
        };
    };
    _u setVariable ["HMT_LASTTAC", _tac];
    _act
};

// DISPATCH : applique le vecteur _tacs a la liste de netIds _ids (1:1)
HMT_TAC_DISPATCH = {
    params ["_ids", "_tacs"];
    {
        private _u = objectFromNetId _x;
        if (!isNull _u && {alive _u}) then { [_u, _tacs select _forEachIndex] call HMT_TAC_EXEC; };
    } forEach _ids;
    count _ids
};

diag_log "HARMATTAN_TACEXEC charge (EXEC / DISPATCH / FLANK_PT)";
