// Battle Lines conduit le combat. Nous, on enregistre le graphe.
if (isServer) then {
    [] spawn {
        sleep 20;                       // laisser Battle Lines poser ses secteurs et ses forces
        [0, 0.2] execVM "hmt_capture.sqf";
    };
    [] spawn {
        sleep 5;
        private _m = [];
        { _m pushBack (configName _x) } forEach ("true" configClasses (configFile >> "CfgPatches"));
        diag_log format ["HMT|MONDE|%1|mods|%2|carte|%3", count _m, (_m joinString ","), worldName];
    };
};
