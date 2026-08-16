HMT_KIT = {
    params ["_u","_role"];
    _u linkItem "rhs_1PN138";
    _u addItem "ACE_EarPlugs";
    _u addItem "ACE_MapTools";
    if ((backpack _u) == "") then { _u addBackpack "rhs_rd54"; };
    if (_role in ["rifleman","at","officer","medic","sergeant"]) then { _u addPrimaryWeaponItem "rhs_acc_1p78"; };
    _u addMagazines ["rhs_mag_rgd5", 2];
    _u addMagazines ["rhs_mag_rdg2_white", 2];
    { _u addItem _x } forEach ["ACE_fieldDressing","ACE_fieldDressing","ACE_fieldDressing","ACE_packingBandage","ACE_packingBandage","ACE_elasticBandage","ACE_tourniquet","ACE_tourniquet","ACE_morphine","ACE_epinephrine","ACE_splint"];
    if (_role == "medic") then {
        { _u addItem _x } forEach ["ACE_surgicalKit","ACE_personalAidKit","ACE_bloodIV","ACE_bloodIV","ACE_bloodIV_500","ACE_salineIV","ACE_salineIV"];
        for "_k" from 1 to 8 do { _u addItem "ACE_fieldDressing"; };
        for "_k" from 1 to 4 do { _u addItem "ACE_morphine"; _u addItem "ACE_epinephrine"; };
    };
    if (_role == "officer") then { _u linkItem "ACE_microDAGR"; };
};
private _grp = createGroup east;
private _r = _grp createUnit ["rhs_msv_rifleman",[2000,5600,0],[],0,"NONE"];
private _m = _grp createUnit ["rhs_msv_medic",[2000,5605,0],[],0,"NONE"];
sleep 1;
[_r,"rifleman"] call HMT_KIT;
[_m,"medic"] call HMT_KIT;
sleep 1;
{
    _x params ["_role","_u"];
    diag_log ("HARMATTAN_KITUP " + _role + " | nvg=" + (hmd _u) + " | optic=" + str (primaryWeaponItems _u) + " | bag=" + (backpack _u) + " | nItems=" + str (count items _u) + " | morphine=" + str ("ACE_morphine" in (items _u)) + " | surg=" + str ("ACE_surgicalKit" in (items _u)) + " | nades=" + str ({_x in ["rhs_mag_rgd5","rhs_mag_rdg2_white"]} count magazines _u));
} forEach [["rifleman",_r],["medic",_m]];
{ deleteVehicle (_x select 1) } forEach [["",_r],["",_m]];
deleteGroup _grp;
diag_log "HARMATTAN_KITUP_DONE";
