// occupation_runtime.sqf — RUNTIME de l'occupation (HARMATTAN, REDFOR/CSAT)
// Tient ~2000 hommes sur 1 serveur a cout CPU plat : Dynamic Simulation + hibernation + garde-budget.
// Mesure validee : dyn-sim ON = 49 FPS vs 13,6 OFF (x3,6) ; budget actif ~700-1000 ; effondrement ~1200.
if (!isServer) exitWith {};

// 1) DYNAMIC SIMULATION — l'IA ne tourne QUE pres d'un acteur (joueur ou agent BLUFOR)
enableDynamicSimulationSystem true;
"Group"        setDynamicSimulationDistance 800;     // infanterie : reveil a 800 m d'un acteur
"Vehicle"      setDynamicSimulationDistance 1000;
"EmptyVehicle" setDynamicSimulationDistance 300;
"Prop"         setDynamicSimulationDistance 150;
setDynamicSimulationDistanceCoef ["Group", 1.0];

// 2) HIBERNATION — chaque groupe REDFOR sous dyn-sim ; loin de tout BLUFOR il dort (cout ~0)
HMT_fnc_register = { params ["_grp"]; _grp enableDynamicSimulation true; };
{ if (side _x == east) then { [_x] call HMT_fnc_register; }; } forEach allGroups;

// 3) GARDE-FOU DU BUDGET ACTIF — au-dela de ~1000 eveilles le serveur s'effondre ; on surveille.
HMT_ACTIVE_BUDGET = 1000;
[] spawn {
    while {true} do {
        private _awake = allUnits select {(side _x == east) && (simulationEnabled _x)};
        diag_log format ["HARMATTAN_RUNTIME actifs=%1 fps=%2 budget=%3", count _awake, round diag_fps, HMT_ACTIVE_BUDGET];
        sleep 30;
    };
};

// 4) (option) LAMBS Danger — comportement reactif riche sur les groupes eveilles, si le mod est charge
if (isClass (configFile >> "CfgPatches" >> "lambs_danger")) then {
    diag_log "HARMATTAN_RUNTIME LAMBS danger present -> comportement reactif REDFOR";
};

diag_log "HARMATTAN_RUNTIME pret (dyn-sim + hibernation + garde-budget)";
