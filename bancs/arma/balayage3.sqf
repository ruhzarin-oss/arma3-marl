// balayage3.sqf — ISOLER. Quatre choses differaient entre le banc muet et le banc qui tire :
// (a) un vrai ENNEMI connu au lieu d un muret, (b) doWatch sur l OBJET au lieu d une position,
// (c) skill 1 au lieu de 0,5, (d) 3 s de repos au lieu de 2. On les separe.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 4;
    HMT_ESSAI = {
        params ["_nom", "_skill", "_repos", "_sur_ennemi"];
        private _o = [4644, 5652];
        private _g = createGroup west;  private _gd = createGroup east;
        private _u = _g createUnit ["B_Soldier_F", [(_o select 0)+10, (_o select 1)-120, 0], [], 0, "NONE"];
        _u setPosATL [(_o select 0)+10, (_o select 1)-120, 0];
        private _e = _gd createUnit ["O_Soldier_F", [(_o select 0)+10, (_o select 1)-60, 0], [], 0, "NONE"];
        _e setPosATL [(_o select 0)+10, (_o select 1)-60, 0];
        _e disableAI "PATH"; _e setBehaviour "CARELESS"; _e allowDamage false;
        _u allowDamage false; _u setSkill _skill;
        _u selectWeapon (primaryWeapon _u);
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setUnitPos "UP";
        _u reveal [_e, 4];
        sleep _repos;
        HMT_N = 0;
        private _eh = _u addEventHandler ["Fired", { HMT_N = HMT_N + 1 }];
        // la CIBLE : soit l ennemi lui-meme, soit une POSITION vide a cote de lui
        private _pos = [(_o select 0)+25, (_o select 1)-60, 0];
        private _t0 = time;
        while { time - _t0 < 8 } do {
            if (_sur_ennemi) then { _u doWatch _e; _u doTarget _e }
                             else { _u doWatch _pos; _u doTarget objNull; _u setDir (_u getDir _pos) };
            _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
            sleep 0.4;
        };
        _u removeEventHandler ["Fired", _eh];
        (format ["HMT|B3|%1|coups|%2|skill|%3|repos|%4|sur_ennemi|%5",
                 _nom, HMT_N, _skill, _repos, _sur_ennemi]) call HMT_LOG;
        deleteVehicle _u; deleteVehicle _e; sleep 1;
    };
    "HMT|B3|debut" call HMT_LOG;
    ["REF_ennemi_skill1_repos3",   1,   3, true ] call HMT_ESSAI;   // la config qui tire
    ["POSITION_au_lieu_d_ennemi",  1,   3, false] call HMT_ESSAI;   // (a)+(b) : LA question
    ["ennemi_skill05",           0.5,   3, true ] call HMT_ESSAI;   // (c)
    ["ennemi_repos2",              1,   2, true ] call HMT_ESSAI;   // (d)
    "HMT|B3|TERMINE" call HMT_LOG;
};
