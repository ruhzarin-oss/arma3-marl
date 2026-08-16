// anomalie.sqf — OU `disableAI "AUTOCOMBAT"` SE FAIT-IL DEFAIRE ?
// Mesure ecrite dans ANOMALIE_AUTOCOMBAT.md : trois lectures du MEME homme, apres chaque
// etape de la mise en scene. La ligne ou il repasse a `true` nomme la cause.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    private _o = [4644, 5652];
    private _g = createGroup west;
    private _u = _g createUnit ["B_Soldier_F", [(_o select 0), (_o select 1) - 170, 0], [], 0, "NONE"];
    _u setPosATL [(_o select 0), (_o select 1) - 170, 0];
    HMT_ENNEMI = []; HMT_FR = [_u];

    HMT_LIRE = {
        params ["_etape", "_u"];
        (format ["HMT|AN|%1|autoc|%2|fsm|%3|path|%4|mode|%5|comport|%6",
                 _etape, _u checkAIFeature "AUTOCOMBAT", _u checkAIFeature "FSM",
                 _u checkAIFeature "PATH", combatMode _u, behaviour _u]) call HMT_LOG;
    };

    "HMT|AN|debut" call HMT_LOG;
    ["0_a_la_creation",        _u] call HMT_LIRE;
    _u setSkill 0.5;
    _u selectWeapon (primaryWeapon _u);
    ["1_apres_selectWeapon",   _u] call HMT_LIRE;
    _u disableAI "AUTOCOMBAT";
    ["2_apres_disableAI_AUTOC", _u] call HMT_LIRE;
    _u disableAI "FSM";
    ["3_apres_disableAI_FSM",  _u] call HMT_LIRE;
    _u setBehaviour "COMBAT";
    ["4_apres_setBehaviour",   _u] call HMT_LIRE;
    _u setCombatMode "RED";
    ["5_apres_setCombatMode",  _u] call HMT_LIRE;
    _u allowFleeing 0;
    ["6_apres_allowFleeing",   _u] call HMT_LIRE;
    sleep 3;
    ["7_apres_3s",             _u] call HMT_LIRE;
    // ── le WAKE du banc, tel qu il est envoye ──
    { _x setBehaviour "AWARE"; _x disableAI "AUTOCOMBAT"; _x disableAI "FSM" } forEach HMT_FR;
    ["8_apres_WAKE",           _u] call HMT_LIRE;
    sleep 5;
    ["9_apres_5s_de_plus",     _u] call HMT_LIRE;
    // ── un ordre de tir, comme l action 9 ──
    _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
    ["10_apres_forceWeaponFire", _u] call HMT_LIRE;
    "HMT|AN|TERMINE" call HMT_LOG;
};
