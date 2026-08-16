// tactics.sqf — ETAPE 4 : EXECUTEURS + DISPATCH. L'orchestration choisit l'index/agent, ceci execute.
// Chaque executeur : params ["_u"] -> calcule sa cible (ennemi connu le plus proche) + garde-fou conso.

HMT_NEAREST_E = { params ["_u"]; _u findNearestEnemy (getPosATL _u) };   // ennemi connu le plus proche

// 0 = TIR VISE : reflex_r23wh tire deja (TARGET) -> on s'assure juste qu'il vise
HMT_TAC_AIMED = { params ["_u"]; _u enableAI "TARGET"; _u setVariable ["HMT_TAC","aimed",true]; true };

// 1 = GRENADE (conso) : jet vers l'ennemi proche, si grenade dispo
HMT_TAC_GRENADE = {
    params ["_u"];
    if ((time - (_u getVariable ["HMT_GREN_T",-99])) < 9) exitWith { false };
    private _e = [_u] call HMT_NEAREST_E; if (isNull _e || {(_u distance _e) > 40}) exitWith { false };
    if (({_x in ["rhs_VOG25","rhs_mag_rgd5","HandGrenade","rhsgref_grenade_rdg2_white"]} count (magazines _u)) == 0) exitWith { false };  // garde-fou conso
    _u setVariable ["HMT_GREN_T", time];
    private _from = (eyePos _u); private _to = (eyePos _e);
    private _g = "rhs_ammo_grenade_rgd5" createVehicle _from;
    private _v = (_from vectorFromTo _to) vectorMultiply 19; _g setVelocity [_v select 0, _v select 1, 8.5];
    _u setVariable ["HMT_TAC","grenade",true]; true
};

// 2 = FLANC : pose un point de flanc que le driver routera (setVariable lu par FobDriver)
HMT_TAC_FLANK = {
    params ["_u"]; private _e = [_u] call HMT_NEAREST_E; if (isNull _e) exitWith { false };
    private _ep = getPosATL _e; private _side = selectRandom [60, -60];
    private _fp = _ep getPos [80, (_ep getDir (getPosATL _u)) + _side];
    _u setVariable ["HMT_FLANK_PT", [_fp select 0, _fp select 1], true];
    _u setVariable ["HMT_TAC","flank",true]; true
};

// 3 = FUMIGENE (conso) : ecran entre l'agent et l'ennemi, si fumi dispo
HMT_TAC_SMOKE = {
    params ["_u"];
    if ((time - (_u getVariable ["HMT_SMOKE_T",-99])) < 12) exitWith { false };
    private _e = [_u] call HMT_NEAREST_E; if (isNull _e) exitWith { false };
    if (({_x in ["rhs_mag_rdg2_white","SmokeShell","rhs_mag_nspd"]} count (magazines _u)) == 0) then {};  // (la fumee est scriptee -> pas de garde-fou strict)
    _u setVariable ["HMT_SMOKE_T", time];
    private _p = getPosATL _u; private _sp = _p getPos [16, _p getDir (getPosATL _e)];
    "SmokeShell" createVehicle [_sp select 0, _sp select 1, 0];
    _u setVariable ["HMT_TAC","smoke",true]; true
};

// 4 = SUPPRESSION : tir nourri sur le secteur ennemi (re-active AUTOCOMBAT)
HMT_TAC_SUPPRESS = {
    params ["_u"]; private _e = [_u] call HMT_NEAREST_E; if (isNull _e) exitWith { false };
    _u enableAI "AUTOCOMBAT"; _u enableAI "TARGET"; _u setUnitPos "MIDDLE"; _u doSuppressiveFire _e;
    _u setVariable ["HMT_TAC","suppress",true]; true
};

// DISPATCH : 5 listes d'index (dans HMT_PILOT) -> applique la tactique de chaque groupe
HMT_DISPATCH = {
    params ["_aimed","_gren","_flank","_smoke","_supp"];
    { private _u = HMT_PILOT select _x; if (!isNull _u && {alive _u}) then { [_u] call HMT_TAC_GRENADE } } forEach _gren;
    { private _u = HMT_PILOT select _x; if (!isNull _u && {alive _u}) then { [_u] call HMT_TAC_FLANK } } forEach _flank;
    { private _u = HMT_PILOT select _x; if (!isNull _u && {alive _u}) then { [_u] call HMT_TAC_SMOKE } } forEach _smoke;
    { private _u = HMT_PILOT select _x; if (!isNull _u && {alive _u}) then { [_u] call HMT_TAC_SUPPRESS } } forEach _supp;
};
diag_log "HARMATTAN_TACTICS executeurs + dispatch charges (aimed/grenade/flank/smoke/suppress)";
