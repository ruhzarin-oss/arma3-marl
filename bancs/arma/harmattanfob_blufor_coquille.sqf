// blufor_coquille.sqf — PONT COQUILLE WEST (inversion BLUFOR full-agent).
// Copie side-flippee de arm_shells.sqf : arme HMT_WPILOT (escouade WEST spawnee par python, loadout 003)
// en coquilles pilotees en velocite. L'ennemi = EAST (les FOB LAMBS). Le tir EMERGE (TARGET garde).
// python : spawn WEST + setUnitLoadout 003 -> remplit HMT_WPILOT -> call HMT_WARM -> boucle HMT_WREAD/HMT_WDVX.

if (isNil "HMT_EMIT") then { HMT_EMIT = { diag_log _this }; };
HMT_WAGENT_MODE = false;
if (isNil "HMT_WPILOT") then { HMT_WPILOT = []; };
if (isNil "HMT_WDVX") then { HMT_WDVX = []; HMT_WDVY = []; HMT_WDDIR = []; };

// lecture : positions des coquilles WEST + ennemis EAST connus (fog realiste, knowsAbout>1)
HMT_WREAD = {
    private _s = "";
    {
        private _u = _x;
        if (!isNull _u) then {
            private _p = getPosATL _u;
            private _ok = [0,1] select (alive _u && !(_u getVariable ["ACE_isUnconscious", false]));
            _s = _s + format ["%1,%2,%3,%4;", round (_p select 0), round (_p select 1), round ((damage _u) * 100), _ok];
        } else { _s = _s + "0,0,100,0;"; };
    } forEach HMT_WPILOT;
    private _en = (allUnits select { (side _x == east) && alive _x && (west knowsAbout _x > 1) }) apply { [round ((getPosATL _x) select 0), round ((getPosATL _x) select 1)] };
    (format ["HARMATTAN_WRX n=%1 mode=%2 en=%3 | %4", count HMT_WPILOT, HMT_WAGENT_MODE, _en, _s]) call HMT_EMIT;
};

// armement : desactive l'IA (LAMBS) + handler EachFrame qui pilote en velocite. Le tir reste autonome (TARGET garde).
HMT_WARM = {
    if (HMT_WAGENT_MODE) exitWith { (format ["HARMATTAN_WARM deja actif"]) call HMT_EMIT; };
    private _act = HMT_WPILOT select { !isNull _x && { alive _x } };
    if (count _act == 0) exitWith { (format ["HARMATTAN_WARM aucun actif"]) call HMT_EMIT; };
    HMT_WPILOT = _act; HMT_WDVX = []; HMT_WDVY = []; HMT_WDDIR = [];
    {
        _x disableAI "FSM"; _x disableAI "AUTOCOMBAT"; _x disableAI "PATH"; _x disableAI "ANIM";
        _x setVariable ["HMT_WSHELL", true];
        HMT_WDVX pushBack 0; HMT_WDVY pushBack 0; HMT_WDDIR pushBack (getDir _x);
    } forEach HMT_WPILOT;
    if (!isNil "HMT_WEF") then { removeMissionEventHandler ["EachFrame", HMT_WEF]; };
    HMT_WEF = addMissionEventHandler ["EachFrame", {
        private _n = count HMT_WPILOT;
        if (_n == 0) exitWith {};
        if (count HMT_WDVX < _n || {count HMT_WDVY < _n} || {count HMT_WDDIR < _n}) exitWith {};
        {
            private _u = _x; private _i = _forEachIndex;
            if (!isNull _u && { alive _u }) then {
                private _vx = HMT_WDVX select _i; private _vy = HMT_WDVY select _i;
                if (!finite _vx) then { _vx = 0 };
                if (!finite _vy) then { _vy = 0 };
                private _vz = (velocity _u) select 2;
                if (!finite _vz) then { _vz = 0 };
                _u setVelocity [_vx, _vy, _vz];
                private _d = HMT_WDDIR select _i;
                if (finite _d) then { _u setDir _d };
            };
        } forEach HMT_WPILOT;
    }];
    HMT_WAGENT_MODE = true;
    (format ["HARMATTAN_WARM pilots=%1 mode=ON", count HMT_WPILOT]) call HMT_EMIT;
};

HMT_WDISARM = {
    if (!HMT_WAGENT_MODE) exitWith { (format ["HARMATTAN_WDISARM pas arme"]) call HMT_EMIT; };
    if (!isNil "HMT_WEF") then { removeMissionEventHandler ["EachFrame", HMT_WEF]; HMT_WEF = nil; };
    {
        if (!isNull _x) then { _x enableAI "FSM"; _x enableAI "AUTOCOMBAT"; _x enableAI "PATH"; _x enableAI "ANIM"; _x setVariable ["HMT_WSHELL", nil]; };
    } forEach HMT_WPILOT;
    HMT_WPILOT = []; HMT_WDVX = []; HMT_WDVY = []; HMT_WDDIR = [];
    HMT_WAGENT_MODE = false;
    (format ["HARMATTAN_WDISARM retour LAMBS"]) call HMT_EMIT;
};

(format ["HARMATTAN_WBRIDGE ok warm=%1 read=%2", !(isNil "HMT_WARM"), !(isNil "HMT_WREAD")]) call HMT_EMIT;
