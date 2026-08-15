// pilote_tire.sqf — les attaquants en mode PILOTE tirent-ils ? Criteres deposes AVANT.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    HMT_BRAS = {
        params ["_nom", "_mode", "_designer"];
        private _o = [4644, 5652];
        private _ga = createGroup west; private _gd = createGroup east;
        private _att = []; private _def = [];
        private _az = random 360;
        for "_i" from 1 to 4 do {
            private _p = [(_o select 0) + 170*sin _az + (((_i-1) mod 2)*6-3),
                          (_o select 1) + 170*cos _az + ((_i-2)*6), 0];
            private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u setSkill 0.5; _u selectWeapon (primaryWeapon _u);
            if (_mode == "pilote") then {
                _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
                _u setBehaviour "AWARE"; _u setCombatMode "BLUE";
            } else {
                _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
            };
            _att pushBack _u;
        };
        for "_i" from 1 to 4 do {
            private _a = random 360; private _r = 10 + random 25;
            private _p = [(_o select 0) + _r*sin _a, (_o select 1) + _r*cos _a, 0];
            private _u = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u setSkill 0.5; _u selectWeapon (primaryWeapon _u);
            _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
            _def pushBack _u;
        };
        { _x allowDamage false } forEach (_att + _def);
        HMT_CA = 0; HMT_CD = 0;
        { _x addEventHandler ["Fired", { HMT_CA = HMT_CA + 1 }] } forEach _att;
        { _x addEventHandler ["Fired", { HMT_CD = HMT_CD + 1 }] } forEach _def;
        { { _x reveal [_y, 4] } forEach _def } forEach _att;
        sleep 2;
        private _t0 = time;
        while { time - _t0 < 60 } do {
            {
                private _u = _x;
                // on les fait AVANCER comme le banc live, par setVelocity reemis
                private _d = (_o select 0) - (getPosATL _u select 0);
                private _e = (_o select 1) - (getPosATL _u select 1);
                private _n = sqrt (_d*_d + _e*_e);
                if (_n > 30) then { _u setVelocity [6*_d/_n, 6*_e/_n, 0] };
                if (_designer) then {
                    private _c = objNull; private _md = 1e9;
                    { if (alive _x) then { private _dd = _u distance _x; if (_dd < _md) then {_md=_dd;_c=_x} } } forEach _def;
                    if (!isNull _c) then { _u reveal [_c, 4]; _u doTarget _c; _u doWatch _c };
                };
            } forEach _att;
            sleep 0.2;
        };
        (format ["HMT|PT|%1|attaquants|%2|defenseurs|%3|dist_finale|%4",
                 _nom, HMT_CA, HMT_CD,
                 round ((getPosATL (_att select 0)) distance2D [_o select 0, _o select 1, 0])]) call HMT_LOG;
        { deleteVehicle _x } forEach (_att + _def);
        sleep 2;
    };
    "HMT|PT|debut" call HMT_LOG;
    ["PILOTE",       "pilote", false] call HMT_BRAS;
    ["NATIF",        "natif",  false] call HMT_BRAS;
    ["PILOTE_CIBLE", "pilote", true ] call HMT_BRAS;
    "HMT|PT|TERMINE" call HMT_LOG;
};
