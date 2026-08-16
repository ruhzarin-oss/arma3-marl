private _r = ["ACRE_PRC343","ACRE_PRC148","ACRE_PRC152","ACRE_PRC117F","ACRE_PRC77","ACRE_SEM52SL","ACRE_SEM70"];
diag_log ("HARMATTAN_ACRE_OK " + str (_r select { isClass (configFile >> "CfgWeapons" >> _x) }));
diag_log ("HARMATTAN_ACRE_MISS " + str (_r select { !isClass (configFile >> "CfgWeapons" >> _x) }));
diag_log "HARMATTAN_ACRE_DONE";
