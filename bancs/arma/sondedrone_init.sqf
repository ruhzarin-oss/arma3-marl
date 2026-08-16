if (isServer) then { [] spawn { sleep 5; HMT_DR_REPS = 2; execVM "sonde_drone.sqf"; }; };
