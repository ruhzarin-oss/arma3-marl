"""Pose le scenario otage sur server14 et le laisse STABLE (pour que tu trouves l'endroit avant la rescousse).
N'IMPORTE PAS b1_loop (qui se lance tout seul) : SPAWN inline, pas de boucle."""
import time
from arma_bridge import ArmaBridge
b = ArmaBridge()

SPAWN = r'''
[] spawn {
  createCenter west; createCenter east; createCenter civilian;
  HMT_C = [20885,16779,0]; HMT_OBJ = HMT_C; HMT_INS = [(HMT_C select 0),(HMT_C select 1)-90,0]; HMT_EXT = HMT_INS; HMT_PICKED = 0;
  if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach (HMT_FR + HMT_GUARDS); if (!isNull HMT_HOSTAGE) then { deleteVehicle HMT_HOSTAGE }; };
  private _civg = createGroup civilian; HMT_HOSTAGE = _civg createUnit ["B_Soldier_F", HMT_C, [], 0, "CAN_COLLIDE"];
  HMT_HOSTAGE setCaptive true; HMT_HOSTAGE disableAI "ALL"; HMT_HOSTAGE setBehaviour "CARELESS"; HMT_HOSTAGE setPosATL HMT_C;
  private _gg = createGroup east; HMT_GUARDS = [];
  for "_i" from 0 to 5 do { private _a=_i*60; private _gp=[(HMT_C select 0)+25*cos _a,(HMT_C select 1)+25*sin _a,0]; private _u=_gg createUnit ["O_Soldier_F",_gp,[],0,"FORM"]; _u disableAI "PATH"; _u setUnitPos "UP"; HMT_GUARDS pushBack _u; };
  private _bg = createGroup west; HMT_FR = [];
  for "_i" from 0 to 8 do { private _sp=[(HMT_INS select 0)+(_i mod 3)*4-4,(HMT_INS select 1)+(floor(_i/3))*4,0]; private _u=_bg createUnit ["B_Soldier_F",_sp,[],0,"NONE"];
     _u disableAI "FSM"; _u disableAI "PATH"; _u disableAI "MOVE"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "SAFE"; _u setUnitPos "UP"; HMT_FR pushBack _u; };
  deleteMarker "hmt_obj"; private _m = createMarker ["hmt_obj", HMT_C]; _m setMarkerType "hd_objective"; _m setMarkerColor "ColorRed"; _m setMarkerText "OTAGE";
  diag_log format ["HARMATTAN_SPAWN fr=%1 g=%2 h=%3", count HMT_FR, count HMT_GUARDS, !isNull HMT_HOSTAGE];
};
'''

b.send(SPAWN, wait=True, timeout=20); time.sleep(2)
u = b.read_obs(timeout=12)
print("scenario STABLE pose : %d unites visibles @ [20885,16779] (marqueur OTAGE)" % len(u))
