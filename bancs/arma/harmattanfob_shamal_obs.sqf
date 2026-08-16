// shamal_obs.sqf — capteur + actuateur pour piloter les soldats WEST (HMT_WPILOT) par la politique SHAMAL.
// ZERO LAMBS : on coupe la FSM danger (= LAMBS), on GARDE le moteur qui vise/tire (doTarget/doSuppressiveFire).
// Python fabrique les 17 features/soldat depuis les champs bruts emis ici, sort une action, la renvoie via HMT_ACTS.
// A charger depuis le dossier MISSION : call compile preprocessFileLineNumbers "shamal_obs.sqf";

// --- ARMEMENT : corps SHAMAL (pas LAMBS) ---
HMT_SHAMAL_ARM = {
    {
        if (!isNull _x) then {
            _x disableAI "FSM";              // coupe la FSM danger = enleve LAMBS
            _x disableAI "AUTOCOMBAT";        // ne pas court-circuiter nos ordres
            { _x enableAI _y } forEach ["MOVE","PATH","TARGET","AUTOTARGET","WEAPONAIM","AIMINGERROR","SUPPRESSION"];
            _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSkill 0.65;
            _x setVariable ["HMT_SHAMAL", true];
        };
    } forEach HMT_WPILOT;
    HMT_WNEAR = [];
    (format ["HARMATTAN_SHARM n=%1", count HMT_WPILOT]) call HMT_EMIT;
};

// --- CAPTEUR : emet les champs bruts par soldat (Python assemble l'obs 17) ---
// par soldat i : px,py (rel FOB), al, cov(0-30), los(0/1), nd, dmg(0-100), thr, pos(0/1/2)
HMT_SHAMAL_SENSE = {
    private _fx = HMT_FOB select 0; private _fy = HMT_FOB select 1;
    private _ens = allUnits select {side _x == east && alive _x};
    HMT_WNEAR = [];
    private _out = "";
    {
        private _u = _x; private _i = _forEachIndex;
        private _p = getPosATL _u;
        private _px = (_p select 0) - _fx; private _py = (_p select 1) - _fy;
        private _al = 0; if (alive _u) then { _al = 1 };
        // ennemi le plus proche + LOS (checkVisibility natif)
        private _en = objNull; private _nd = 999;
        { private _d = _u distance _x; if (_d < _nd) then { _nd = _d; _en = _x }; } forEach _ens;
        HMT_WNEAR set [_i, _en];
        private _los = 0; private _thr = 0;
        if (!isNull _en) then {
            if (([objNull, "VIEW"] checkVisibility [eyePos _u, eyePos _en]) > 0.3) then { _los = 1 };
        };
        // menace : nb d'ennemis vivants a portee ET qui me voient
        {
            if ((_u distance _x) < 110) then {
                if (([objNull, "VIEW"] checkVisibility [eyePos _x, eyePos _u]) > 0.3) then { _thr = _thr + 1 };
            };
        } forEach _ens;
        // proxy couvert : distance au bati/obstacle le plus proche (capee 30)
        private _cov = 30;
        { private _cd = _u distance _x; if (_cd < _cov) then { _cov = _cd }; } forEach (nearestTerrainObjects [_p, ["HOUSE","BUILDING","WALL","ROCK","TREE","BUSH","FENCE"], 30]);
        private _dmg = round ((damage _u) * 100);
        private _st = stance _u; private _pos = 0;
        if (_st == "CROUCH") then { _pos = 1 }; if (_st == "PRONE") then { _pos = 2 };
        _out = _out + format ["%1,%2,%3,%4,%5,%6,%7,%8,%9;", round _px, round _py, _al, round _cov, _los, round _nd, _dmg, _thr, _pos];
    } forEach HMT_WPILOT;
    (format ["HARMATTAN_SHS n=%1 | %2", count HMT_WPILOT, _out]) call HMT_EMIT;
};

// --- ACTUATEUR : applique HMT_ACTS (une action par soldat) ---
// 0-7 = cap (deplacement), 8 = HOLD, 9 = SUPPRESS (feu), 10/11/12 = posture debout/accroupi/couche
HMT_SHAMAL_APPLY = {
    {
        private _u = _x; private _i = _forEachIndex;
        if (alive _u && _i < count HMT_ACTS) then {
            private _a = HMT_ACTS select _i;
            if (_a < 8) then {
                private _dir = _a * 45;
                private _tgt = (getPosATL _u) vectorAdd [22 * sin _dir, 22 * cos _dir, 0];
                _u setUnitPos "AUTO"; _u doMove _tgt; _u forceSpeed -1;
            } else {
                if (_a == 9) then {
                    private _en = HMT_WNEAR select _i;
                    if (!isNull _en) then { _u doWatch _en; _u doTarget _en; _u doSuppressiveFire _en; };
                } else {
                    if (_a == 8) then { doStop _u; };
                    if (_a == 10) then { _u setUnitPos "UP"; };
                    if (_a == 11) then { _u setUnitPos "MIDDLE"; };
                    if (_a == 12) then { _u setUnitPos "DOWN"; };
                };
            };
        };
    } forEach HMT_WPILOT;
};
