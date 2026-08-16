// anomalie2.sqf — l ENGAGEMENT SOUTENU reactive-t-il AUTOCOMBAT ?
// Le pas-a-pas dit `false` partout ; la sonde du temoin lisait `true` APRES 12 s de
// reveal + doTarget + tir force + setVelocity. On lit donc AVANT, PENDANT et APRES.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    private _o = [4644, 5652];
    private _g = createGroup west; private _gd = createGroup east;
    private _u = _g createUnit ["B_Soldier_F", [(_o select 0), (_o select 1) - 170, 0], [], 0, "NONE"];
    _u setPosATL [(_o select 0), (_o select 1) - 170, 0];
    _u setSkill 0.5; _u selectWeapon (primaryWeapon _u);
    _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
    _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0; _u allowDamage false;
    private _e = _gd createUnit ["O_Soldier_F", [(_o select 0), (_o select 1) - 130, 0], [], 0, "NONE"];
    _e setPosATL [(_o select 0), (_o select 1) - 130, 0];
    _e disableAI "PATH"; _e setBehaviour "CARELESS"; _e allowDamage false;

    HMT_L = { params ["_q","_u"]; (format ["HMT|A2|%1|autoc|%2|fsm|%3", _q, _u checkAIFeature "AUTOCOMBAT", _u checkAIFeature "FSM"]) call HMT_LOG };

    "HMT|A2|debut" call HMT_LOG;
    ["0_avant_tout", _u] call HMT_L;
    _u reveal [_e, 4];
    ["1_apres_reveal", _u] call HMT_L;
    _u doTarget _e;
    ["2_apres_doTarget", _u] call HMT_L;
    _u doWatch _e;
    ["3_apres_doWatch", _u] call HMT_L;
    private _t0 = time;
    while { time - _t0 < 6 } do { _u doWatch _e; _u doTarget _e;
        _u forceWeaponFire [currentWeapon _u, currentMuzzle _u]; sleep 0.33 };
    ["4_apres_6s_de_tir_force", _u] call HMT_L;
    private _t1 = time;
    while { time - _t1 < 4 } do { _u setVelocity [0, 6, 0]; sleep 0.1 };
    ["5_apres_4s_de_setVelocity", _u] call HMT_L;
    _u doTarget objNull; _u doWatch objNull;
    ["6_apres_doTarget_objNull", _u] call HMT_L;
    "HMT|A2|TERMINE" call HMT_LOG;
};
