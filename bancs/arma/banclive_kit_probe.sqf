private _roles = ["rhs_msv_rifleman","rhs_msv_machinegunner","rhs_msv_at","rhs_msv_marksman","rhs_msv_medic","rhs_msv_officer"];
private _grp = createGroup east;
private _us = [];
{ private _u = _grp createUnit [_x, [2000,5600,0], [], 0, "NONE"]; _us pushBack [_x, _u]; } forEach _roles;
sleep 2;
{
  _x params ["_role","_u"];
  if (isNull _u) then { diag_log ("HARMATTAN_KIT " + _role + " NULL"); } else {
    diag_log ("HARMATTAN_KIT " + _role + " | wpn=" + (primaryWeapon _u) + " | wItems=" + str (primaryWeaponItems _u) + " | launcher=" + (secondaryWeapon _u) + " | head=" + (headgear _u) + " | vest=" + (vest _u) + " | bag=" + (backpack _u) + " | nvg=" + (hmd _u) + " | assigned=" + str (assignedItems _u));
    diag_log ("HARMATTAN_KIT2 " + _role + " | items=" + str (items _u) + " | nmag=" + str (count magazines _u));
  };
} forEach _us;
{ deleteVehicle (_x select 1) } forEach _us;
deleteGroup _grp;
diag_log "HARMATTAN_KIT_DONE";
