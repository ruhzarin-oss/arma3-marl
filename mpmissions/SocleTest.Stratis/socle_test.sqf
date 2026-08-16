// socle_test.sqf — LE PREVOL SAIT-IL ECHOUER ?
//   ⟨Fable⟩ « Un audit qui ne sait pas echouer ne prouve rien. »
// Six cas : un monde SAIN qui doit passer VERT, et cinq fuites volontaires dont chacune
// doit faire ROUGIR le prevol sur SON test. Un prevol qui laisse passer une fuite est mort.
call compile preprocessFileLineNumbers "socle.sqf";

[] spawn {
    sleep 4;
    private _o = [4644, 5652];
    private _g = createGroup west;
    private _res = [];

    HMT_CAS = {
        params ["_nom", "_attendu", "_saboter"];
        private _o = [4644, 5652];
        private _g = createGroup west;
        private _h = [];
        for "_i" from 1 to 3 do {
            private _p = [(_o select 0) + _i*5, (_o select 1) - 120, 0];
            _h pushBack ([_g, "B_Soldier_F", _p, "pilote"] call HMT_POSER_HOMME);
        };
        { _x allowDamage false } forEach _h;
        sleep 2;
        [_h] call _saboter;                       // ── LA FUITE ──
        sleep 1;
        private _vert = [_h] call HMT_PREVOL;
        private _bon = (_vert == _attendu);
        (format ["HMT|ST|CAS|%1|attendu|%2|obtenu|%3|%4", _nom,
                 (if (_attendu) then {"VERT"} else {"ROUGE"}),
                 (if (_vert) then {"VERT"} else {"ROUGE"}),
                 (if (_bon) then {"OK"} else {"RATE"})]) call HMT_LOG;
        { deleteVehicle _x } forEach _h;
        sleep 1;
        _bon
    };

    "HMT|ST|debut" call HMT_LOG;
    _res pushBack (["0_monde_sain",      true,  { }] call HMT_CAS);
    _res pushBack (["T1_arme_au_sac",    false, { { removeAllWeapons _x } forEach (_this select 0) }] call HMT_CAS);
    _res pushBack (["T2_chargeur_vide",  false, { { _x setVehicleAmmo 0 } forEach (_this select 0) }] call HMT_CAS);
    _res pushBack (["T3_FSM_recoupee",   false, { { _x disableAI "PATH" } forEach (_this select 0) }] call HMT_CAS);
    _res pushBack (["T4_ne_tire_pas",    false, { { _x disableAI "FIREWEAPON" } forEach (_this select 0) }] call HMT_CAS);
    _res pushBack (["T5_immobile",       false, { { _x disableAI "MOVE"; _x setVariable ["hmt_mode","statue",true] } forEach (_this select 0) }] call HMT_CAS);
    // CLIQUET : la faute du 15/08 au soir devient un test permanent.
    _res pushBack (["T6_combatMode_BLUE", false, { { _x setCombatMode "BLUE" } forEach (_this select 0) }] call HMT_CAS);

    private _n = { _x } count _res;
    (format ["HMT|ST|BILAN|%1|sur|%2", _n, count _res]) call HMT_LOG;
    "HMT|ST|TERMINE" call HMT_LOG;
};
