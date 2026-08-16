// balayage2.sqf — QUELLE COMMANDE FAIT PARTIR UNE BALLE ?
// Le balayage des ETATS a rendu zero partout (arme en main, haute, COMBAT/RED, sans
// disableAI, ennemi revele). Ce n est donc pas l etat : c est la COMMANDE.
// On balaie donc les commandes, config identique, cible reelle a 60 m.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    private _o = [4644, 5652];

    HMT_ESSAI = {
        params ["_nom", "_tirer"];
        private _o = [4644, 5652];
        private _g = createGroup west;  private _gd = createGroup east;
        private _u = _g createUnit ["B_Soldier_F", [(_o select 0)+10, (_o select 1)-120, 0], [], 0, "NONE"];
        _u setPosATL [(_o select 0)+10, (_o select 1)-120, 0];
        private _e = _gd createUnit ["O_Soldier_F", [(_o select 0)+10, (_o select 1)-60, 0], [], 0, "NONE"];
        _e setPosATL [(_o select 0)+10, (_o select 1)-60, 0];
        _e disableAI "PATH"; _e setBehaviour "CARELESS"; _e allowDamage false;
        _u allowDamage false; _u setSkill 1;
        _u selectWeapon (primaryWeapon _u);
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setUnitPos "UP";
        _u reveal [_e, 4];
        sleep 3;
        HMT_N = 0;
        private _eh = _u addEventHandler ["Fired", { HMT_N = HMT_N + 1 }];
        private _t0 = time;
        while { time - _t0 < 8 } do { [_u, _e] call _tirer; sleep 0.4 };
        _u removeEventHandler ["Fired", _eh];
        (format ["HMT|B2|%1|coups|%2|posture|%3", _nom, HMT_N, animationState _u]) call HMT_LOG;
        deleteVehicle _u; deleteVehicle _e; sleep 1;
    };

    "HMT|B2|debut" call HMT_LOG;
    ["1_forceWeaponFire", { params ["_u","_e"];
        _u doWatch _e; _u forceWeaponFire [currentWeapon _u, currentMuzzle _u] }] call HMT_ESSAI;
    ["2_fireAtTarget",    { params ["_u","_e"];
        _u doTarget _e; _u fireAtTarget [_e, currentMuzzle _u] }] call HMT_ESSAI;
    ["3_doFire",          { params ["_u","_e"];
        _u doTarget _e; _u doFire _e }] call HMT_ESSAI;
    ["4_fire_muzzle",     { params ["_u","_e"];
        _u doWatch _e; _u fire (currentMuzzle _u) }] call HMT_ESSAI;
    ["5_rien_que_l_IA",   { params ["_u","_e"];
        _u doTarget _e }] call HMT_ESSAI;
    "HMT|B2|TERMINE" call HMT_LOG;
};
