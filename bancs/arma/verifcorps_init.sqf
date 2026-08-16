if (isServer) then { [] spawn { sleep 4; call compile preprocessFileLineNumbers "ordre.sqf"; execVM "verif_corps.sqf"; }; };
