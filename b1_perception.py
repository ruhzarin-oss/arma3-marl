"""B1 etape 3 — PERCEPTION 29-obs en SQF, calibree sur le replica (S=140, centre Altis [20885,16779]).
Repere sandbox = Arma : px=Est=ax-cx, py=Nord=ay-cy, 1 unite = 1 m. Couvert = batiments (lineIntersectsSurfaces).
On respawn propre, on GELE les amis (disableAI) pour une lecture stable, on log les 29 obs/agent, on VERIFIE la sanite."""
import time, re
from arma_bridge import ArmaBridge

CX, CY, S = 20885.0, 16779.0, 140.0
b = ArmaBridge()

SPAWN = r'''
[] spawn {
  createCenter west; createCenter east; createCenter civilian;
  HMT_C = [20885, 16779, 0];
  HMT_OBJ = HMT_C;
  HMT_INS = [(HMT_C select 0), (HMT_C select 1) - 90, 0];   // insertion 90 m au sud (dans le patch)
  HMT_EXT = HMT_INS;
  if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach (HMT_FR + HMT_GUARDS); if (!isNull HMT_HOSTAGE) then { deleteVehicle HMT_HOSTAGE }; };
  private _civg = createGroup civilian;
  HMT_HOSTAGE = _civg createUnit ["B_Soldier_F", HMT_C, [], 0, "CAN_COLLIDE"];
  HMT_HOSTAGE setCaptive true; HMT_HOSTAGE disableAI "ALL"; HMT_HOSTAGE setBehaviour "CARELESS"; HMT_HOSTAGE setUnitPos "UP"; HMT_HOSTAGE setPosATL HMT_C;
  private _gg = createGroup east; HMT_GUARDS = [];
  for "_i" from 0 to 5 do { private _a=_i*60; private _gp=[(HMT_C select 0)+25*cos _a,(HMT_C select 1)+25*sin _a,0]; private _u=_gg createUnit ["O_Soldier_F",_gp,[],0,"FORM"]; HMT_GUARDS pushBack _u; };
  private _bg = createGroup west; HMT_FR = [];
  for "_i" from 0 to 8 do { private _sp=[(HMT_INS select 0)+(_i mod 3)*4-4,(HMT_INS select 1)+(floor(_i/3))*4,0]; private _u=_bg createUnit ["B_Soldier_F",_sp,[],0,"NONE"];
     _u disableAI "FSM"; _u disableAI "PATH"; _u disableAI "MOVE"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "CARELESS"; _u setUnitPos "UP"; HMT_FR pushBack _u; };
  diag_log format ["HARMATTAN_SPAWN fr=%1 g=%2 h=%3", count HMT_FR, count HMT_GUARDS, !isNull HMT_HOSTAGE];
};
'''

# Perception : pour chaque ami, 29 obs dans le repere sandbox. coque = 12 rayons centres sur la menace (lineIntersectsSurfaces).
PERC = r'''
HMT_S = 140; HMT_CX = 20885; HMT_CY = 16779;
{
  private _u = _x; private _i = _forEachIndex;
  private _p = getPosATL _u; private _ax = (_p select 0)-HMT_CX; private _ay = (_p select 1)-HMT_CY;
  private _hp = getPosATL HMT_HOSTAGE; private _hx=(_hp select 0)-HMT_CX; private _hy=(_hp select 1)-HMT_CY;
  private _dhx=_hx-_ax; private _dhy=_hy-_ay; private _dh=sqrt(_dhx*_dhx+_dhy*_dhy)+0.001;
  private _ex=(HMT_EXT select 0)-HMT_CX-_ax; private _ey=(HMT_EXT select 1)-HMT_CY-_ay; private _de=sqrt(_ex*_ex+_ey*_ey)+0.001;
  // garde vivant le plus proche
  private _ng=objNull; private _nd=1e9; { if (alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_nd) then {_nd=_d; _ng=_x}; }; } forEach HMT_GUARDS;
  private _gdx=0; private _gdy=0; private _gd=1; private _los=0;
  if (!isNull _ng) then { private _q=getPosATL _ng; _gdx=((_q select 0)-HMT_CX)-_ax; _gdy=((_q select 1)-HMT_CY)-_ay; _gd=sqrt(_gdx*_gdx+_gdy*_gdy)+0.001;
     private _gp=getPosASL _ng; private _aps=getPosASL _u; _los = if (terrainIntersectASL [[(_aps select 0),(_aps select 1),(_aps select 2)+0.9],[(_gp select 0),(_gp select 1),(_gp select 2)+0.9]]) then {0} else {1}; };
  // coequipier vivant le plus proche
  private _nt=objNull; private _td=1e9; { if (_x != _u && alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_td) then {_td=_d; _nt=_x}; }; } forEach HMT_FR;
  private _tdx=0; private _tdy=0; private _tdist=1;
  if (!isNull _nt) then { private _q=getPosATL _nt; _tdx=((_q select 0)-HMT_CX)-_ax; _tdy=((_q select 1)-HMT_CY)-_ay; _tdist=sqrt(_tdx*_tdx+_tdy*_tdy)+0.001; };
  // coque 12 rayons centres sur la menace
  private _th0 = if (!isNull _ng) then { _gdy atan2 _gdx } else { 0 };
  private _shell = [];
  for "_k" from 0 to 11 do { private _ang=_th0+_k*30; private _ddx=cos _ang; private _ddy=sin _ang; private _sv=1;
     for "_s" from 1 to 20 do { private _r=_s/20*60; private _qx=(_p select 0)+_r*_ddx; private _qy=(_p select 1)+_r*_ddy;
        if (count (nearestObjects [[_qx,_qy,(_p select 2)], ["House","Wall","Rock"], 3]) > 0) exitWith { _sv=_s/20 }; };
     _shell pushBack _sv; };
  private _dmg = damage _u;
  // 29 = shell(12)+dmg + toh(3)+toe(3)+gobs(4)+tobs(3)+pk+hh+oh
  private _o = _shell + [_dmg, _dhx/_dh, _dhy/_dh, (_dh/HMT_S) min 2, _ex/_de, _ey/_de, (_de/HMT_S) min 2,
     _gdx/_gd, _gdy/_gd, (_gd/HMT_S) min 2, _los, _tdx/_tdist, _tdy/_tdist, (_tdist/HMT_S) min 2,
     0, damage HMT_HOSTAGE, _dmg];
  diag_log format ["HARMATTAN_AOBS %1 %2", _i, _o];
} forEach HMT_FR;
'''


def read_aobs(bridge, timeout=15):
    n = bridge.send(PERC, wait=True, timeout=timeout)
    time.sleep(0.8)
    lines = bridge._log_lines()
    idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    obs = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_AOBS (\d+) \[([^\]]+)\]", ln)
        if m:
            obs[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
    return [obs[k] for k in sorted(obs)]


print("spawn...", flush=True)
b.send(SPAWN, wait=True, timeout=20); time.sleep(3)
o = read_aobs(b)
print("agents percus:", len(o), flush=True)
if o:
    a0 = o[0]
    print("agent0 obs len:", len(a0), flush=True)
    print("  coque(12):", [round(x, 2) for x in a0[:12]], flush=True)
    print("  dmg:", round(a0[12], 2), flush=True)
    print("  toh dir+dist:", [round(x, 2) for x in a0[13:16]], "(otage au Nord => toh_y>0 attendu)", flush=True)
    print("  toe dir+dist:", [round(x, 2) for x in a0[16:19]], flush=True)
    print("  garde dir+dist+los:", [round(x, 2) for x in a0[19:23]], flush=True)
    print("  coequipier:", [round(x, 2) for x in a0[23:26]], flush=True)
    print("  pk/hh/oh:", [round(x, 2) for x in a0[26:29]], flush=True)
    import math
    ok = (a0[15] <= 2.01 and a0[14] > 0 and all(0 <= x <= 1.001 for x in a0[:12]))
    print("SANITE:", "OK" if ok else "A REVOIR", flush=True)
