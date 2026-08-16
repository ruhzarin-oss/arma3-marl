// combo.sqf — QUELLE COMBINAISON rend le FEU sans rendre les JAMBES ?
// `disableAI AUTOCOMBAT` retire la faculte d engager (mesure du 15/08 : 0 coup contre 127).
// Mais `disableAI FSM` sert a empecher l IA de piloter le deplacement a la place de la
// politique. On cherche donc la combinaison qui TIRE et qui se laisse DEPLACER.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    HMT_BRAS = {
        params ["_nom", "_autocombat", "_fsm"];
        private _o = [4644, 5652];
        private _ga = createGroup west; private _gd = createGroup east;
        private _att = []; private _def = [];
        private _az = random 360;
        for "_i" from 1 to 4 do {
            private _p = [(_o select 0) + 170*sin _az + (((_i-1) mod 2)*6-3),
                          (_o select 1) + 170*cos _az + ((_i-2)*6), 0];
            private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u setSkill 0.5; _u selectWeapon (primaryWeapon _u);
            if (!_autocombat) then { _u disableAI "AUTOCOMBAT" };
            if (!_fsm)        then { _u disableAI "FSM" };
            _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
            _att pushBack _u;
        };
        for "_i" from 1 to 4 do {
            private _a = random 360; private _r = 10 + random 25;
            private _p = [(_o select 0) + _r*sin _a, (_o select 1) + _r*cos _a, 0];
            private _u = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u setSkill 0.5; _u selectWeapon (primaryWeapon _u);
            _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setCombatMode "RED";
            _def pushBack _u;
        };
        { _x allowDamage false } forEach (_att + _def);
        HMT_CA = 0;
        { _x addEventHandler ["Fired", { HMT_CA = HMT_CA + 1 }] } forEach _att;
        sleep 2;
        // ── ON PILOTE LE DEPLACEMENT COMME LE BANC : cap fixe vers l objectif, 6 m/s ──
        private _d0 = (getPosATL (_att select 0)) distance2D [_o select 0, _o select 1, 0];
        private _t0 = time;
        while { time - _t0 < 45 } do {
            {
                private _u = _x;
                private _dx = (_o select 0) - (getPosATL _u select 0);
                private _dy = (_o select 1) - (getPosATL _u select 1);
                private _n = sqrt (_dx*_dx + _dy*_dy);
                if (_n > 30) then { _u setVelocity [6*_dx/_n, 6*_dy/_n, 0] };
            } forEach _att;
            sleep 0.1;
        };
        private _d1 = (getPosATL (_att select 0)) distance2D [_o select 0, _o select 1, 0];
        (format ["HMT|CO|%1|coups|%2|gagne_m|%3|autocombat|%4|fsm|%5",
                 _nom, HMT_CA, round (_d0 - _d1), _autocombat, _fsm]) call HMT_LOG;
        { deleteVehicle _x } forEach (_att + _def);
        sleep 2;
    };
    "HMT|CO|debut" call HMT_LOG;
    ["A_actuel_les_deux_coupes", false, false] call HMT_BRAS;
    ["B_AUTOCOMBAT_rendu",       true,  false] call HMT_BRAS;
    ["C_FSM_rendu",              false, true ] call HMT_BRAS;
    ["D_les_deux_rendus",        true,  true ] call HMT_BRAS;
    "HMT|CO|TERMINE" call HMT_LOG;
};
