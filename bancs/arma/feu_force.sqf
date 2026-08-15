// feu_force.sqf — l appui existe-t-il vraiment sur Arma ? Criteres dans DEPOT_FEU_FORCE.md
HMT_LOG = { diag_log _this };

HMT_APPUYER = {
    params ["_u", "_pos", ["_duree", 5]];
    private _t0 = time;
    while { alive _u && time - _t0 < _duree } do {
        _u setDir (_u getDir _pos);
        _u doWatch _pos;
        _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
        sleep 0.33;
    };
    _u doWatch objNull;
};

[] spawn {
    sleep 4;
    private _o = [4644, 5652];
    // le tireur
    private _gb = createGroup west;
    private _t = _gb createUnit ["B_Soldier_F", [(_o select 0), (_o select 1) - 150, 0], [], 0, "NONE"];
    _t setPosATL [(_o select 0), (_o select 1) - 150, 0];
    _t disableAI "AUTOCOMBAT"; _t disableAI "FSM"; _t disableAI "PATH";
    _t setBehaviour "AWARE"; _t setCombatMode "BLUE"; _t allowDamage false;
    _t setSkill 0.5;
    // la cible, derriere un muret
    private _gd = createGroup east;
    private _c = _gd createUnit ["O_Soldier_F", _o, [], 0, "NONE"];
    _c setPosATL [_o select 0, _o select 1, 0];
    _c disableAI "PATH"; _c setBehaviour "COMBAT"; _c setCombatMode "RED"; _c allowFleeing 0;
    private _mur = createVehicle ["Land_CncBarrierMedium_F", [(_o select 0), (_o select 1) - 4, 0], [], 0, "CAN_COLLIDE"];
    _mur setDir 90;
    private _vise = [(_o select 0), (_o select 1) - 4, 1];

    // compteurs : chaque coup est horodate et attribue a une FENETRE
    HMT_COUPS = [];
    _t addEventHandler ["Fired", { HMT_COUPS pushBack [time, missionNamespace getVariable ["HMT_FEN", "silence"]] }];
    HMT_RIPOSTE = [];
    _c addEventHandler ["Fired", { HMT_RIPOSTE pushBack [time, missionNamespace getVariable ["HMT_FEN", "silence"]] }];

    sleep 3;
    "HMT|FF|debut" call HMT_LOG;

    {
        private _bras = _x;
        for "_cy" from 1 to 10 do {
            // ── FENETRE D ORDRE, 5 s ──
            HMT_FEN = "ordre";
            private _s0 = count HMT_COUPS;
            if (_bras == "A_command") then {
                _t commandSuppressiveFire _mur;
                sleep 5;
            } else {
                [_t, _vise, 5] call HMT_APPUYER;
            };
            private _sup = getSuppression _c;
            // ── FENETRE DE SILENCE, 5 s : rien n est demande ──
            HMT_FEN = "silence";
            _t doTarget objNull; _t doWatch objNull;
            sleep 5;
            (format ["HMT|FF|CY|%1|%2|ordre|%3|silence|%4|supp|%5|riposte|%6",
                     _bras, _cy,
                     ({(_x select 1) == "ordre"} count HMT_COUPS),
                     ({(_x select 1) == "silence"} count HMT_COUPS),
                     _sup, count HMT_RIPOSTE]) call HMT_LOG;
        };
    } forEach ["A_command", "B_force"];

    // ── CONTROLE POSITIF : la meme boucle sur une cible A DECOUVERT doit TUER ──
    deleteVehicle _mur;
    private _c2 = _gd createUnit ["O_Soldier_F", [(_o select 0) + 3, _o select 1, 0], [], 0, "NONE"];
    _c2 setPosATL [(_o select 0) + 3, _o select 1, 0];
    _c2 disableAI "PATH"; _c2 setBehaviour "CARELESS";
    sleep 2;
    HMT_FEN = "controle";
    private _t0 = time;
    while { alive _c2 && time - _t0 < 40 } do { [_t, getPosATL _c2, 5] call HMT_APPUYER; sleep 0.5 };
    (format ["HMT|FF|CONTROLE|cible_a_decouvert_tuee|%1|en|%2|s",
             (if (alive _c2) then {0} else {1}), round (time - _t0)]) call HMT_LOG;
    "HMT|FF|TERMINE" call HMT_LOG;
};
