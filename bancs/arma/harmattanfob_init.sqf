diag_log "HARMATTAN_FOB_INIT leviathan001 demarre";

// ---------------------------------------------------------------------------------------
// HMT_MONDE_PLEIN — interrupteur de la CONSTRUCTION DU MONDE (garnisons des 25 FOB,
// patrouilles, monde vivant). Une session SHAMAL les avait eteints en commentant trois
// lignes a la main (`// DESACTIVE-SHAMAL`) ; rallumes le 11/08/2026 pour le banc de pression
// de l'officier de theatre — sans eux le SITREP repond 0 garnison / 0 cible et rien n'est
// mesurable. Pour re-eteindre : passer cette seule ligne a false.
// Sauvegarde de l'etat precedent : init.sqf.avant_pression_20260811
HMT_MONDE_PLEIN = true;
// ---------------------------------------------------------------------------------------

// === SERVEUR : pont fichier+natif, monde, garnisons ===
if (isServer) then {
[] spawn {
    call compile preprocessFileLineNumbers "harmattan_actuator.sqf";
    diag_log "HARMATTAN_FOB_PONT actuateur fichier charge";
    if (("hmt_native" callExtension "version") != "") then {
        call compile preprocessFileLineNumbers "harmattan_actuator_native.sqf";
        HMT_EMIT = { diag_log _this; "hmt_native" callExtension ("o|" + _this); };   // les reponses partent AUSSI en TCP (pas de troncature 1024)
        diag_log "HARMATTAN pont NATIF actif (TCP 5816)";
    };
    sleep 5;
    { _x params ["_n","_v"]; missionNamespace setVariable [_n, _v, true]; } forEach [["ace_medical_fractures",2],["ace_medical_limping",2],["ace_medical_bleedingCoefficient",1.5],["ace_medical_painCoefficient",1.5],["ace_medical_spontaneousWakeUpChance",0.05],["ace_medical_statemachine_cardiacArrestTime",180],["ace_medical_ai_enabledFor",2],["ace_medical_blood_enabledFor",2]];
    if (HMT_MONDE_PLEIN) then { call compile preprocessFileLineNumbers "fob_network.sqf"; };
    diag_log "HARMATTAN_FOB_INIT build appele";
    sleep 2;
    call compile preprocessFileLineNumbers "roles.sqf";          // ETAPE 3 : roles + arsenal ACE par role
    sleep 1;
    if (HMT_MONDE_PLEIN) then { call compile preprocessFileLineNumbers "fob_life.sqf"; };
    sleep 1;
    if (HMT_MONDE_PLEIN) then { call compile preprocessFileLineNumbers "world_alive.sqf"; };
    sleep 1;
    call compile preprocessFileLineNumbers "logistics_objectives.sqf";
    sleep 1;
    call compile preprocessFileLineNumbers "defense_eval.sqf";
    call compile preprocessFileLineNumbers "arm_shells.sqf";
    call compile preprocessFileLineNumbers "tactics.sqf";        // ETAPE 4 : executeurs des tactiques
    call compile preprocessFileLineNumbers "map_overlay.sqf";
    call compile preprocessFileLineNumbers "orch_features.sqf";   // extracteur 10 features + snapshot orchestration
    call compile preprocessFileLineNumbers "tactics_exec.sqf";    // executeurs des 5 tactiques (dispatch)
    call compile preprocessFileLineNumbers "officer_sit.sqf";     // SITREP en fonction (HMT_SITREP)
    sleep 2;
    // caisse ARSENAL (ACE si dispo, sinon arsenal virtuel BIS) au spawn du slot WEST attaquant
    private _ars = "Box_NATO_Equip_F" createVehicle [3600, 3850, 0];
    _ars allowDamage false; _ars setPosATL [3600, 3850, 0];
    if (!isNil "ace_arsenal_fnc_initBox") then { [_ars, true] call ace_arsenal_fnc_initBox; } else { ["AmmoboxInit", [_ars, true]] call BIS_fnc_arsenal; };
    HMT_ARSENAL = _ars;
    diag_log "HARMATTAN_ARSENAL caisse arsenal posee au spawn WEST [3600,3850]";
    call compile preprocessFileLineNumbers "caserne_sud.sqf";   // CASERNE OTAN (west) au sud + arsenal ACE — durable
    // DEGEL : monde plein des le boot (choix Younes) — plus de gel dyn-sim
    { _x enableSimulation true; _x enableDynamicSimulation false; } forEach allUnits;
    { _x enableSimulation true; _x enableDynamicSimulation false; } forEach vehicles;
    diag_log format ["HARMATTAN_DEGEL monde plein (dyn-sim off) actif=%1", {simulationEnabled _x} count allUnits];
    diag_log format ["HARMATTAN_DIFF third=%1 map=%2 medFract=%3 timeMult=%4", difficultyEnabled "third", difficultyEnabled "map", ace_medical_fractures, timeMultiplier];
};
};

// === HEADLESS CLIENT : son pont natif (port = son HMT_EXT_PORT) + les fonctions locales ===
if (!isServer && !hasInterface) then {
    call compile preprocessFileLineNumbers "arm_shells.sqf";                 // HMT_ARM_LOCAL / READ / DISARM
    HMT_EMIT = { diag_log _this; "hmt_native" callExtension ("o|" + _this); };   // dual : HMT_READ du HC sort sur SON pont
    call compile preprocessFileLineNumbers "harmattan_actuator_native.sqf";  // pont natif de CE HC
    "hmt_native" callExtension "o|HARMATTAN_HC_READY";
};
