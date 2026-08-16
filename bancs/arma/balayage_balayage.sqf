// balayage.sqf — POURQUOI AUCUNE BALLE NE PART. On ne devine plus : on balaie.
// Deux diagnostics faux sur ce banc (capteur aveugle, puis arme au sac — l arme EST en main
// et rien ne part). Donc mesure DIAGNOSTIQUE : plusieurs configurations, une seule passe.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    private _o = [4644, 5652];
    private _g = createGroup west;
    private _cible = [(_o select 0), (_o select 1) + 60, 0];

    HMT_ESSAI = {
        params ["_nom", "_prep"];
        private _o = [4644, 5652];
        private _g = createGroup west;
        private _u = _g createUnit ["B_Soldier_F", [(_o select 0)+10, (_o select 1)-120, 0], [], 0, "NONE"];
        _u setPosATL [(_o select 0)+10, (_o select 1)-120, 0];
        _u allowDamage false; _u setSkill 0.5;
        _u selectWeapon (primaryWeapon _u);
        [_u] call _prep;
        sleep 2;
        HMT_N = 0;
        private _eh = _u addEventHandler ["Fired", { HMT_N = HMT_N + 1 }];
        private _c = [(_o select 0)+10, (_o select 1)-60, 0];
        private _t0 = time;
        while { time - _t0 < 6 } do {
            _u setDir (_u getDir _c); _u doWatch _c;
            _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
            sleep 0.33;
        };
        _u removeEventHandler ["Fired", _eh];
        (format ["HMT|BAL|%1|coups|%2|arme|%3|levee|%4|comport|%5|mode|%6|etat|%7",
                 _nom, HMT_N, currentWeapon _u,
                 (if (weaponLowered _u) then {"BASSE"} else {"HAUTE"}),
                 behaviour _u, combatMode _u, animationState _u]) call HMT_LOG;
        deleteVehicle _u; sleep 1;
    };

    "HMT|BAL|debut" call HMT_LOG;
    ["A_aware_blue_disable3", { params ["_u"];
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u disableAI "PATH";
        _u setBehaviour "AWARE"; _u setCombatMode "BLUE" }] call HMT_ESSAI;
    ["B_combat_red_disable3", { params ["_u"];
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u disableAI "PATH";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED" }] call HMT_ESSAI;
    ["C_combat_red_aucun_disable", { params ["_u"];
        _u setBehaviour "COMBAT"; _u setCombatMode "RED" }] call HMT_ESSAI;
    ["D_arme_levee_forcee", { params ["_u"];
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED";
        _u action ["WeaponOnBack", _u]; sleep 0.5; _u action ["SwitchWeapon", _u, _u, 0] }] call HMT_ESSAI;
    ["E_avec_ennemi_revele", { params ["_u"];
        _u setBehaviour "COMBAT"; _u setCombatMode "RED";
        private _o = [4644, 5652];
        private _gd = createGroup east;
        private _e = _gd createUnit ["O_Soldier_F", [(_o select 0)+10, (_o select 1)-60, 0], [], 0, "NONE"];
        _e setPosATL [(_o select 0)+10, (_o select 1)-60, 0]; _e disableAI "PATH";
        _u reveal [_e, 4]; _u doTarget _e }] call HMT_ESSAI;
    "HMT|BAL|TERMINE" call HMT_LOG;
};
