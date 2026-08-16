// B : coquilles pilotables (DEFINITIONS, n arme pas au chargement)
if (isNil "HMT_EMIT") then { HMT_EMIT = { diag_log _this }; };   // defaut fichier ; le pont natif override en diag_log+o|
HMT_AGENT_MODE = false;
if (isNil "HMT_PILOT") then { HMT_PILOT = []; };
if (isNil "HMT_DVX") then { HMT_DVX = []; HMT_DVY = []; HMT_DDIR = []; };

HMT_READ = {
    private _s = "";
    {
        private _u = _x;
        if (!isNull _u) then {
            private _p = getPosATL _u;
            private _ok = [0,1] select (alive _u && !(_u getVariable ["ACE_isUnconscious", false]));
            _s = _s + format ["%1,%2,%3,%4;", round (_p select 0), round (_p select 1), round ((damage _u) * 100), _ok];
        } else { _s = _s + "0,0,100,0;"; };
    } forEach HMT_PILOT;
    private _en = (allUnits select { (side _x != east) && (side _x != civilian) && alive _x && (east knowsAbout _x > 1) }) apply { [round ((getPosATL _x) select 0), round ((getPosATL _x) select 1)] };
    (format ["HARMATTAN_RX n=%1 mode=%2 en=%3 | %4", count HMT_PILOT, HMT_AGENT_MODE, _en, _s]) call HMT_EMIT;
};

HMT_ARM = {
    if (HMT_AGENT_MODE) exitWith { diag_log "HARMATTAN_ARM deja actif"; };
    private _act = (HMT_FOB_MEN apply { _x select 0 }) select { !isNull _x && { alive _x } && { simulationEnabled _x } };
    if (count _act == 0) exitWith { diag_log "HARMATTAN_ARM aucun actif"; };
    if (count _act > 50) then { _act = _act select [0, 50]; };   // 50 agents appris ; le reste = LAMBS (FPS jouable + monde plein)
    HMT_PILOT = _act; HMT_DVX = []; HMT_DVY = []; HMT_DDIR = [];
    {
        _x disableAI "FSM"; _x disableAI "AUTOCOMBAT"; _x disableAI "PATH"; _x disableAI "ANIM";
        _x setVariable ["HMT_SHELL", true];
        HMT_DVX pushBack 0; HMT_DVY pushBack 0; HMT_DDIR pushBack (getDir _x);
    } forEach HMT_PILOT;
    removeAllMissionEventHandlers "EachFrame";                       // tue tout handler fuite avant d'en remettre un
    HMT_EF = addMissionEventHandler ["EachFrame", {
        private _n = count HMT_PILOT;
        if (_n == 0) exitWith {};
        if (count HMT_DVX < _n || {count HMT_DVY < _n} || {count HMT_DDIR < _n}) exitWith {};   // securite desync
        {
            private _u = _x; private _i = _forEachIndex;
            if (!isNull _u && { alive _u }) then {
                private _vx = HMT_DVX select _i; private _vy = HMT_DVY select _i;
                if (!finite _vx) then { _vx = 0 };
                if (!finite _vy) then { _vy = 0 };
                private _vz = (velocity _u) select 2;
                if (!finite _vz) then { _vz = 0 };               // la velocite Z peut etre NaN (corrompue) -> setVelocity erreur
                _u setVelocity [_vx, _vy, _vz];
                private _d = HMT_DDIR select _i;
                if (finite _d) then { _u setDir _d };
            };
        } forEach HMT_PILOT;
    }];
    HMT_AGENT_MODE = true;
    diag_log format ["HARMATTAN_ARM pilots=%1 mode=ON", count HMT_PILOT];
};

HMT_DISARM = {
    if (!HMT_AGENT_MODE) exitWith { diag_log "HARMATTAN_DISARM pas arme"; };
    removeAllMissionEventHandlers "EachFrame"; HMT_EF = nil;         // tue TOUS les handlers (y compris fuites)
    {
        if (!isNull _x) then { _x enableAI "FSM"; _x enableAI "AUTOCOMBAT"; _x enableAI "PATH"; _x enableAI "ANIM"; _x setVariable ["HMT_SHELL", nil]; };
    } forEach HMT_PILOT;
    HMT_PILOT = []; HMT_DVX = []; HMT_DVY = []; HMT_DDIR = [];
    HMT_AGENT_MODE = false;
    diag_log "HARMATTAN_DISARM retour LAMBS";
};

// ===== HEADLESS CLIENTS : repartir la physique sur K coeurs =====
// SERVEUR : reveille les garnisons puis distribue les groupes east sur les HC (ownership reseau).
HMT_DISTRIBUTE = {
    { private _u = _x select 0; if (!isNull _u) then { _u enableSimulation true; _u enableDynamicSimulation false; }; } forEach HMT_FOB_MEN;
    private _hcs = entities "HeadlessClient_F";
    if (count _hcs == 0) exitWith { diag_log "HMT: aucun HC connecte"; };
    private _grps = allGroups select {side _x == east && {alive _x && simulationEnabled _x} count units _x > 0};
    { _x setGroupOwner (owner (_hcs select (_forEachIndex mod (count _hcs)))); } forEach _grps;
    diag_log format ["HMT_DISTRIBUTE %1 groupes -> %2 HC", count _grps, count _hcs];
};

// CHAQUE HC : arme ses unites LOCALES (handler durci finite+longueur), emet par SON pont natif.
HMT_ARM_LOCAL = {
    if (HMT_AGENT_MODE) exitWith {};
    private _act = allUnits select {local _x && side _x == east && alive _x && simulationEnabled _x};
    if (count _act > 130) then { _act = _act select [0, 130]; };
    if (count _act == 0) exitWith { "hmt_native" callExtension "o|HARMATTAN_HC_ARM 0"; };
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
            if (!isNull _x && {alive _x}) then {
                private _i = _forEachIndex;
                private _vx = HMT_DVX select _i; if (!finite _vx) then { _vx = 0 };
                private _vy = HMT_DVY select _i; if (!finite _vy) then { _vy = 0 };
                private _vz = (velocity _x) select 2; if (!finite _vz) then { _vz = 0 };
                _x setVelocity [_vx, _vy, _vz];
                private _d = HMT_DDIR select _i; if (finite _d) then { _x setDir _d };
            };
        } forEach HMT_PILOT;
    }];
    HMT_AGENT_MODE = true;
    "hmt_native" callExtension ("o|HARMATTAN_HC_ARM " + str (count HMT_PILOT));
};

diag_log "HARMATTAN_SHELLS definitions chargees";
