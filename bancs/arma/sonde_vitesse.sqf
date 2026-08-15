// sonde_vitesse.sqf — setVelocity : impulsion ou consigne ? Criteres deposes AVANT.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 3;
    private _o = [4644, 5652];
    private _g = createGroup west;
    private _u = _g createUnit ["B_Soldier_F", [(_o select 0), (_o select 1) - 150, 0], [], 0, "NONE"];
    _u setPosATL [(_o select 0), (_o select 1) - 150, 0];
    // MEME reglage que le banc live : AUTOCOMBAT et FSM coupes, PATH garde
    _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
    _u setBehaviour "AWARE"; _u setCombatMode "BLUE";
    _u allowDamage false;
    sleep 3;
    "HMT|SV|debut" call HMT_LOG;

    {
        private _bras = _x;
        for "_p" from 1 to 10 do {
            _u setPosATL [(_o select 0), (_o select 1) - 150, 0];
            _u setVelocity [0,0,0];
            sleep 1.5;
            private _d0 = getPosATL _u;
            private _t0 = time;
            // ── LE BRAS ──
            if (_bras == "A_une_fois") then {
                _u setVelocity [0, 6, 0];
                sleep 3.28;
            };
            if (_bras == "B_10Hz") then {
                while { time - _t0 < 3.28 } do { _u setVelocity [0, 6, 0]; sleep 0.1; };
            };
            if (_bras == "C_aucune") then { sleep 3.28; };
            private _d1 = getPosATL _u;
            (format ["HMT|SV|PT|%1|periode|%2|metres|%3",
                     _bras, _p, (_d0 distance2D _d1)]) call HMT_LOG;
        };
    } forEach ["A_une_fois", "B_10Hz", "C_aucune"];
    "HMT|SV|TERMINE" call HMT_LOG;
};
