"""Pilote d6 sur les unites DEJA EN PLACE (pas de re-spawn -> ne casse pas la vue du spectateur).
Reveille les gardes (combat), puis boucle perception 29-obs -> d6 -> setVelocity. Pour le LIVE regarde."""
import sys, time, re, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"
b = ArmaBridge()

WAKE = r'''
HMT_PICKED = 0;
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO" } forEach HMT_GUARDS;
{ _x setBehaviour "AWARE" } forEach HMT_FR;
diag_log "HARMATTAN_WAKE gardes reveilles, escouade prete";
'''

PERC = r'''
HMT_S = 140; HMT_CX = 20885; HMT_CY = 16779;
{
  private _u=_x; private _i=_forEachIndex; private _p=getPosATL _u; private _ax=(_p select 0)-HMT_CX; private _ay=(_p select 1)-HMT_CY;
  private _hp=getPosATL HMT_HOSTAGE; private _hx=(_hp select 0)-HMT_CX; private _hy=(_hp select 1)-HMT_CY;
  private _dhx=_hx-_ax; private _dhy=_hy-_ay; private _dh=sqrt(_dhx*_dhx+_dhy*_dhy)+0.001;
  private _ex=(HMT_EXT select 0)-HMT_CX-_ax; private _ey=(HMT_EXT select 1)-HMT_CY-_ay; private _de=sqrt(_ex*_ex+_ey*_ey)+0.001;
  private _ng=objNull; private _nd=1e9; { if (alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_nd) then {_nd=_d;_ng=_x}; }; } forEach HMT_GUARDS;
  private _gdx=0; private _gdy=0; private _gd=1; private _los=0;
  if (!isNull _ng) then { private _q=getPosATL _ng; _gdx=((_q select 0)-HMT_CX)-_ax; _gdy=((_q select 1)-HMT_CY)-_ay; _gd=sqrt(_gdx*_gdx+_gdy*_gdy)+0.001;
     private _gp=getPosASL _ng; private _aps=getPosASL _u; _los=if (terrainIntersectASL [[(_aps select 0),(_aps select 1),(_aps select 2)+0.9],[(_gp select 0),(_gp select 1),(_gp select 2)+0.9]]) then {0} else {1}; };
  private _nt=objNull; private _td=1e9; { if (_x!=_u && alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_td) then {_td=_d;_nt=_x}; }; } forEach HMT_FR;
  private _tdx=0; private _tdy=0; private _tdist=1;
  if (!isNull _nt) then { private _q=getPosATL _nt; _tdx=((_q select 0)-HMT_CX)-_ax; _tdy=((_q select 1)-HMT_CY)-_ay; _tdist=sqrt(_tdx*_tdx+_tdy*_tdy)+0.001; };
  private _th0=if (!isNull _ng) then { _gdy atan2 _gdx } else {0}; private _shell=[];
  for "_k" from 0 to 11 do { private _ang=_th0+_k*30; private _ddx=cos _ang; private _ddy=sin _ang; private _sv=1;
     for "_s" from 1 to 20 do { private _r=_s/20*60; private _qx=(_p select 0)+_r*_ddx; private _qy=(_p select 1)+_r*_ddy;
        if (count (nearestObjects [[_qx,_qy,(_p select 2)],["House","Wall","Rock"],3])>0) exitWith {_sv=_s/20}; };
     _shell pushBack _sv; };
  private _dmg=damage _u; private _pk=if (isNil "HMT_PICKED") then {0} else {HMT_PICKED};
  private _o=_shell+[_dmg,_dhx/_dh,_dhy/_dh,(_dh/HMT_S) min 2,_ex/_de,_ey/_de,(_de/HMT_S) min 2,_gdx/_gd,_gdy/_gd,(_gd/HMT_S) min 2,_los,_tdx/_tdist,_tdy/_tdist,(_tdist/HMT_S) min 2,_pk,damage HMT_HOSTAGE,_dmg];
  diag_log format ["HARMATTAN_AOBS %1 %2", _i, _o];
} forEach HMT_FR;
'''

ACT_TPL = r'''
HMT_CX=20885; HMT_CY=16779; HMT_ACT = [__ACTS__]; HMT_SPD = 6;
{ private _i=_forEachIndex; private _a=HMT_ACT select _i;
  if (_a < 8) then { private _ang=_a*45; _x setVelocity [HMT_SPD*sin _ang, HMT_SPD*cos _ang, 0]; } else { _x setVelocity [0,0,0]; };
} forEach HMT_FR;
private _car=objNull; private _cd=1e9; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_cd) then {_cd=_d;_car=_x}; }; } forEach HMT_FR;
if (_cd < 25) then { HMT_PICKED=1; };
if (HMT_PICKED==1 && !isNull _car) then { HMT_HOSTAGE setPosATL (getPosATL _car) };
private _dex=HMT_HOSTAGE distance2D [(HMT_EXT select 0),(HMT_EXT select 1),0];
private _succ=if (HMT_PICKED==1 && _dex<25) then {1} else {0};
diag_log format ["HARMATTAN_STATUS picked=%1 succ=%2 dh=%3 dex=%4 alive=%5", HMT_PICKED, _succ, round _cd, round _dex, ({alive _x} count HMT_FR)];
'''


def read_aobs(timeout=15):
    n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.6)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    obs = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_AOBS (\d+) \[([^\]]+)\]", ln)
        if m: obs[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
    return torch.tensor([obs[k] for k in sorted(obs)], dtype=torch.float32) if obs else None


def send_act(acts, timeout=15):
    sqf = ACT_TPL.replace("__ACTS__", ",".join(str(int(a)) for a in acts))
    n = b.send(sqf, wait=True, timeout=timeout); time.sleep(0.4)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_STATUS picked=(\d+) succ=(\d+) dh=(-?\d+) dex=(-?\d+) alive=(\d+)", ln)
        if m: return {"picked": int(m.group(1)), "succ": int(m.group(2)), "dh": int(m.group(3)), "dex": int(m.group(4)), "alive": int(m.group(5))}
    return None


net = Net(29, 10, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); net.eval()
b.send(WAKE, wait=True, timeout=15); time.sleep(1)
print("=== d6 EN COMMANDE (live) ===", flush=True)
for t in range(240):
    obs = read_aobs()
    if obs is None: break
    with torch.no_grad(): act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
    st = send_act(act.tolist())
    if t % 10 == 0: print("t=%d %s" % (t, st), flush=True)
    if st and st["succ"]: print(">>> RESCOUSSE REUSSIE t=%d <<<" % t, flush=True); break
    if st and st["alive"] == 0: print(">>> escouade aneantie t=%d" % t, flush=True); break
print("FIN", flush=True)
