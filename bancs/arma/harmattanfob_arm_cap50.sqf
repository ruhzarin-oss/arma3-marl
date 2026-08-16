// arm_cap50.sqf — redefinit HMT_ARM avec un cap a 50 (nom neuf -> contourne le cache preprocessFileLineNumbers).
HMT_ARM = {
    if (HMT_AGENT_MODE) exitWith { diag_log "HARMATTAN_ARM deja actif"; };
    private _act = (HMT_FOB_MEN apply { _x select 0 }) select { !isNull _x && { alive _x } && { simulationEnabled _x } };
    if (count _act == 0) exitWith { diag_log "HARMATTAN_ARM aucun actif"; };
    if (count _act > 50) then { _act = _act select [0, 50]; };
    HMT_PILOT = _act; HMT_DVX = []; HMT_DVY = []; HMT_DDIR = [];
    {
        _x disableAI "FSM"; _x disableAI "AUTOCOMBAT"; _x disableAI "PATH"; _x disableAI "ANIM";
        _x setVariable ["HMT_SHELL", true];
        HMT_DVX pushBack 0; HMT_DVY pushBack 0; HMT_DDIR pushBack (getDir _x);
    } forEach HMT_PILOT;
    removeAllMissionEventHandlers "EachFrame";
    HMT_EF = addMissionEventHandler ["EachFrame", {
        private _n = count HMT_PILOT;
        if (_n == 0) exitWith {};
        if (count HMT_DVX < _n || {count HMT_DVY < _n} || {count HMT_DDIR < _n}) exitWith {};
        {
            private _u = _x; private _i = _forEachIndex;
            if (!isNull _u && { alive _u }) then {
                private _vx = HMT_DVX select _i; private _vy = HMT_DVY select _i;
                if (!finite _vx) then { _vx = 0 };
                if (!finite _vy) then { _vy = 0 };
                private _vz = (velocity _u) select 2;
                if (!finite _vz) then { _vz = 0 };
                _u setVelocity [_vx, _vy, _vz];
                private _d = HMT_DDIR select _i;
                if (finite _d) then { _u setDir _d };
            };
        } forEach HMT_PILOT;
    }];
    HMT_AGENT_MODE = true;
    diag_log format ["HARMATTAN_ARM pilots=%1 mode=ON (cap50)", count HMT_PILOT];
};
diag_log "HMT_ARM_CAP50 applique";
