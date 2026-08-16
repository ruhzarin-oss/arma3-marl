// sonde_temoin.sqf — le temoin du socle contre un attaquant de la scene, MEME passe.
call compile preprocessFileLineNumbers "socle.sqf";
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 4;
    private _o = [4644, 5652];
    private _az = random 360;

    HMT_MESURER = {
        params ["_nom", "_u"];
        private _p = getPosATL _u;
        // arme
        private _arme = currentWeapon _u;
        // coups en 6 s sur un mannequin a 45 m
        private _gd = createGroup east;
        private _m = _gd createUnit ["O_Soldier_F", [(_p select 0), (_p select 1) + 45, 0], [], 0, "NONE"];
        _m setPosATL [(_p select 0), (_p select 1) + 45, 0];
        _m disableAI "PATH"; _m setBehaviour "CARELESS"; _m allowDamage false;
        _u reveal [_m, 4]; sleep 2;
        HMT_N = 0;
        private _eh = _u addEventHandler ["Fired", { HMT_N = HMT_N + 1 }];
        private _t0 = time;
        while { time - _t0 < 6 } do { _u doWatch _m; _u doTarget _m;
            _u forceWeaponFire [currentWeapon _u, currentMuzzle _u]; sleep 0.33 };
        _u removeEventHandler ["Fired", _eh];
        // metres en 4 s
        _u doTarget objNull; _u doWatch objNull;
        private _p0 = getPosATL _u; private _t1 = time;
        while { time - _t1 < 4 } do { _u setVelocity [0, 6, 0]; sleep 0.1 };
        private _d = _p0 distance2D (getPosATL _u);
        (format ["HMT|TE|%1|arme|%2|coups|%3|metres|%4|hauteur|%5|pente|%6|fsm|%7|autoc|%8|path|%9|groupe|%10",
                 _nom, (if (_arme == "") then {"AUCUNE"} else {"oui"}), HMT_N, round _d,
                 round (getTerrainHeightASL [_p select 0, _p select 1]),
                 round (100 * ([_p select 0, _p select 1] call HMT_G_SLOPE)) / 100,
                 _u checkAIFeature "FSM", _u checkAIFeature "AUTOCOMBAT", _u checkAIFeature "PATH",
                 count (units (group _u))]) call HMT_LOG;
        deleteVehicle _m; deleteGroup _gd;
    };

    "HMT|TE|debut" call HMT_LOG;

    // ── A · LE TEMOIN, exactement comme le socle le pose ──
    private _gt = createGroup west;
    private _pt = [(_o select 0) + 300, (_o select 1) + 300, 0];
    private _tem = [_gt, "B_Soldier_F", _pt, "pilote"] call HMT_POSER_HOMME;
    _tem allowDamage false;
    sleep 1;
    ["A_TEMOIN_du_socle", _tem] call HMT_MESURER;

    // ── B · UN ATTAQUANT, exactement comme la scene le pose ──
    private _ga = createGroup west;
    private _pa = [(_o select 0) + 170*sin _az, (_o select 1) + 170*cos _az, 0];
    private _att = _ga createUnit ["B_Soldier_F", _pa, [], 0, "NONE"];
    _att setPosATL _pa; _att setSkill 0.5;
    _att selectWeapon (primaryWeapon _att);
    _att disableAI "AUTOCOMBAT"; _att disableAI "FSM";
    _att setBehaviour "COMBAT"; _att setCombatMode "RED"; _att allowFleeing 0;
    _att allowDamage false;
    sleep 1;
    ["B_ATTAQUANT_de_la_scene", _att] call HMT_MESURER;

    // ── C · LE TEMOIN, mais pose AU LIEU DE LA SCENE (isole la cause « lieu ») ──
    private _gc = createGroup west;
    private _pc = [(_o select 0) + 170*sin (_az + 20), (_o select 1) + 170*cos (_az + 20), 0];
    private _tc = [_gc, "B_Soldier_F", _pc, "pilote"] call HMT_POSER_HOMME;
    _tc allowDamage false;
    sleep 1;
    ["C_TEMOIN_au_lieu_de_la_scene", _tc] call HMT_MESURER;

    "HMT|TE|TERMINE" call HMT_LOG;
};
