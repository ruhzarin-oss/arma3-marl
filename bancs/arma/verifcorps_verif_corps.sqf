// controle positif de la greffe : le banc doit retrouver ~20 m par periode.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 3;
    private _o = [4644, 5652];
    private _g = createGroup west;
    HMT_FR = [];
    private _u = _g createUnit ["B_Soldier_F", [(_o select 0), (_o select 1)-150, 0], [], 0, "NONE"];
    _u setPosATL [(_o select 0), (_o select 1)-150, 0];
    _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
    _u setBehaviour "AWARE"; _u setCombatMode "BLUE"; _u allowDamage false;
    HMT_FR pushBack _u; HMT_POST = [0]; HMT_ENNEMI = [];
    sleep 3;
    "HMT|VC|debut" call HMT_LOG;
    private _fps = [];
    for "_p" from 1 to 10 do {
        _u setPosATL [(_o select 0), (_o select 1)-150, 0]; _u setVelocity [0,0,0];
        sleep 1.2;
        private _d0 = getPosATL _u;
        // ── EXACTEMENT ce que le banc envoie : action 0 = cap nord ──
        call HMT_ORDRE;
        sleep 3.28;
        _fps pushBack diag_fps;
        (format ["HMT|VC|PT|%1|metres|%2|fps|%3", _p, (_d0 distance2D (getPosATL _u)), diag_fps]) call HMT_LOG;
    };
    "HMT|VC|TERMINE" call HMT_LOG;
};
