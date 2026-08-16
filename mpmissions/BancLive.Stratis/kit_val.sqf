private _cw = ["rhs_1PN138","rhs_1PN138_2","rhs_acc_pkas","rhs_acc_1p78","rhs_acc_1p63","rhs_acc_ekp8_02","ACE_fieldDressing","ACE_packingBandage","ACE_elasticBandage","ACE_tourniquet","ACE_morphine","ACE_epinephrine","ACE_bloodIV","ACE_bloodIV_500","ACE_splint","ACE_surgicalKit","ACE_personalAidKit","ACE_EarPlugs","ACE_MapTools","ACE_microDAGR","ACE_salineIV"];
diag_log ("HARMATTAN_VAL_CW_OK " + str (_cw select { isClass (configFile >> "CfgWeapons" >> _x) }));
diag_log ("HARMATTAN_VAL_CW_MISS " + str (_cw select { !isClass (configFile >> "CfgWeapons" >> _x) }));
private _cm = ["rhs_mag_rgd5","rhs_mag_rgn","rhs_mag_rdg2_white","rhs_mag_rdg2_black","rhs_mag_nspd"];
diag_log ("HARMATTAN_VAL_CM_OK " + str (_cm select { isClass (configFile >> "CfgMagazines" >> _x) }));
private _cb = ["rhs_rd54","rhs_assault_umbts","rhs_sidor","rhs_assault_umbts_engineer","rhs_rk_sht_30_emr"];
diag_log ("HARMATTAN_VAL_CB_OK " + str (_cb select { isClass (configFile >> "CfgVehicles" >> _x) }));
diag_log "HARMATTAN_VAL_DONE";
