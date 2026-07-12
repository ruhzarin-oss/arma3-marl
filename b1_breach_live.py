"""BRECHE EN ARMA REEL (server14). 1 sentinelle isolee (face exterieur) + 1 infiltrateur pose sur l'arc arriere.
L'infiltrateur se faufile dans l'ANGLE MORT (obs breche 28-dim exacte) et, en position (proche+dos+non-vu),
execute le TAKEDOWN silencieux : la sentinelle tombe (setDamage 1). Politique = breach_d1.pt (primitive 100%)."""
import os
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Altis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"; CKPT = "/home/younes/compose-embodiment/breach_d1.pt"
b = ArmaBridge()

SETUP = r'''
HMT_CX=20885; HMT_CY=16779;
if (!isNil "HMT_STG_GUARDS") then { { deleteVehicle _x } forEach HMT_STG_GUARDS; };
if (!isNil "HMT_STG_INF") then { if (!isNull HMT_STG_INF) then { deleteVehicle HMT_STG_INF } };
private _ge = createGroup east; HMT_STG_GUARDS=[];
private _gang=0; private _gx=HMT_CX+50*sin _gang; private _gy=HMT_CY+50*cos _gang;   // sentinelle a 50 m, regarde dehors
_ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"];
private _u=(units _ge) select (count (units _ge)-1);
_u setPosATL [_gx,_gy,0]; _u setDir _gang;
{ _u disableAI _x } forEach ["MOVE","PATH","FSM","TARGET","AUTOTARGET","AUTOCOMBAT","ANIM"];
_u setBehaviour "AWARE"; _u setUnitPos "UP"; _u setCombatMode "BLUE";
HMT_STG_GUARDS pushBack _u;
private _gw = createGroup west;                                                      // infiltrateur sur l'arc ARRIERE (cote centre), 50 m
private _rear=_gang+180; private _ix=_gx+50*sin _rear; private _iy=_gy+50*cos _rear;
_gw createUnit ["B_Soldier_F",[_ix,_iy,0],[],0,"NONE"];
HMT_STG_INF=(units _gw) select (count (units _gw)-1);
HMT_STG_INF setPosATL [_ix,_iy,0]; HMT_STG_INF allowDamage false;
{ HMT_STG_INF disableAI _x } forEach ["AUTOTARGET","TARGET","AUTOCOMBAT","FSM","COVER","SUPPRESSION","CHECKVISIBLE"];
HMT_STG_INF enableAI "MOVE"; HMT_STG_INF enableAI "PATH"; HMT_STG_INF setBehaviour "CARELESS";
HMT_STG_INF setUnitPos "AUTO"; HMT_STG_INF forceSpeed 4; HMT_STG_INF setCombatMode "BLUE";
diag_log format ["HARMATTAN_SETUP guard=%1 infpos=%2", getPosATL _u, getPosATL HMT_STG_INF];
'''

PERC = r'''
HMT_S=140; HMT_CX=20885; HMT_CY=16779; HMT_FOV=25; HMT_DR=70;
private _u=HMT_STG_INF; private _p=getPosATL _u; private _aps=getPosASL _u;
private _ax=(_p#0)-HMT_CX; private _ay=(_p#1)-HMT_CY; private _d=sqrt(_ax*_ax+_ay*_ay)+0.000001;
private _tox=-_ax/_d; private _toy=-_ay/_d; private _tod=(_d/HMT_S) min 2;
private _expo=0; private _det=0; private _ngx=0; private _ngy=0; private _ngd2=1e18; private _nge=0;
{
  if (alive _x) then {
    private _q=getPosATL _x; private _gx=(_q#0)-HMT_CX; private _gy=(_q#1)-HMT_CY;
    private _dx=_ax-_gx; private _dy=_ay-_gy; private _dist=sqrt(_dx*_dx+_dy*_dy)+0.000001;
    private _angp=_dy atan2 _dx; private _gf=_gy atan2 _gx;
    private _off=abs(_angp-_gf); if (_off>180) then {_off=360-_off};
    private _gps=getPosASL _x;
    private _los=if (terrainIntersectASL [[(_gps#0),(_gps#1),(_gps#2)+1.6],[(_aps#0),(_aps#1),(_aps#2)+0.9]]) then {0} else {1};
    private _inr=if (_dist<HMT_DR) then {1} else {0};
    if (_off<HMT_FOV && _inr>0 && _los>0.5) then {_det=1};
    private _e=((1-_off/HMT_FOV) max 0)*_inr*_los; _expo=_expo max _e;
    if (_dist*_dist<_ngd2) then {_ngd2=_dist*_dist; _ngx=_gx-_ax; _ngy=_gy-_ay; _nge=_e};
  };
} forEach HMT_STG_GUARDS;
private _ngd=sqrt(_ngx*_ngx+_ngy*_ngy)+0.000001; private _th0=_ngy atan2 _ngx; private _shell=[];
for "_k" from 0 to 11 do {
  private _a2=_th0+_k*30; private _ddx=cos _a2; private _ddy=sin _a2; private _sv=1;
  for "_s" from 1 to 20 do { private _r=_s/20*60; private _qx=(_p#0)+_r*_ddx; private _qy=(_p#1)+_r*_ddy;
    if (count (nearestObjects [[_qx,_qy,_p#2],["House","Wall","Rock"],3])>0) exitWith {_sv=_s/20}; };
  _shell pushBack _sv;
};
private _dmg=damage _u;
private _tg=HMT_STG_GUARDS select 0; private _tq=getPosATL _tg; private _tgx=(_tq#0)-HMT_CX; private _tgy=(_tq#1)-HMT_CY;
private _tdx=_tgx-_ax; private _tdy=_tgy-_ay; private _tdist=sqrt(_tdx*_tdx+_tdy*_tdy)+0.000001;
private _tangp=(_ay-_tgy) atan2 (_ax-_tgx); private _tgf=_tgy atan2 _tgx;
private _toff=abs(_tangp-_tgf); if (_toff>180) then {_toff=360-_toff};
private _tbehind=((_toff-HMT_FOV)/(180-HMT_FOV)) max 0 min 1; private _talive=if (alive _tg) then {1} else {0};
private _o=_shell+[_dmg,_tox,_toy,_tod,_ngx/_ngd,_ngy/_ngd,(_ngd/HMT_S) min 2,_nge,_expo,_det,_dmg,_tdx/_tdist,_tdy/_tdist,(_tdist/HMT_S) min 2,_tbehind,_talive];
diag_log format ["HARMATTAN_BOBS %1", _o];
'''

ACT_TPL = r'''
private _a=__A__; private _u=HMT_STG_INF; private _p=getPosATL _u;
if (_a < 8) then { private _ang=_a*45; _u doMove [(_p#0)+6*sin _ang,(_p#1)+6*cos _ang,0]; } else { _u doMove (getPosATL _u); };
diag_log "HARMATTAN_STEP ok";
'''

TAKEDOWN = r'''
private _tg=HMT_STG_GUARDS select 0; _tg setDamage 1;
diag_log format ["HARMATTAN_TD cible neutralisee pos=%1", getPosATL _tg];
'''


def read_bobs(timeout=15):
    n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.5)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    for ln in reversed(lines[idx:]):
        m = re.search(r"HARMATTAN_BOBS \[([^\]]+)\]", ln)
        if m: return torch.tensor([[float(v) for v in m.group(1).split(",")]], dtype=torch.float32)
    return None


def send_act(a, timeout=15):
    b.send(ACT_TPL.replace("__A__", str(int(a))), wait=True, timeout=timeout); time.sleep(0.9)


net = Net(28, 10, 512, 3).to(DEV); net.load_state_dict(torch.load(CKPT, map_location=DEV)); net.eval()
print("=== BRECHE LIVE sur ARMA (server14) | 1 sentinelle isolee, takedown silencieux ===", flush=True)
for ep in range(3):
    b.send(SETUP, wait=True, timeout=15); time.sleep(2.0)
    alert = 0; res = "timeout"
    for t in range(80):
        obs = read_bobs()
        if obs is None: print("  [obs None t=%d]" % t, flush=True); break
        det = obs[0, 21].item(); tdist = obs[0, 25].item() * 140.0; behind = obs[0, 26].item(); talive = obs[0, 27].item()
        if det > 0.5: alert += 1
        ready = (tdist < 10.0) and (behind > 0.32) and (det < 0.5) and (talive > 0.5)
        if t % 4 == 0: print("  ep%d t=%2d | dist_cible=%4.1fm | dos=%.2f | vu=%d (cumul %d) | pret=%s" % (ep, t, tdist, behind, int(det), alert, ready), flush=True)
        if alert > 3: res = "ALARME (repere)"; print(">>> ep%d : ALARME t=%d" % (ep, t), flush=True); break
        if ready:
            b.send(TAKEDOWN, wait=True, timeout=15); res = "SENTINELLE NEUTRALISEE (silencieux)"
            print(">>> ep%d : TAKEDOWN t=%d (dist %.1fm, dos %.2f, jamais alarme) <<<" % (ep, t, tdist, behind), flush=True); break
        with torch.no_grad(): a = int(net.a_logits(obs).argmax(-1)[0])
        send_act(a)
    print(">>> EP %d : %s | vu cumul=%d" % (ep, res, alert), flush=True)
    if res.startswith("SENTINELLE"): break
print("FIN BRECHE LIVE", flush=True)
