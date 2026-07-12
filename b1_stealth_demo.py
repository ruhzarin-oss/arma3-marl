"""DEMO LIVE en BOUCLE sur server14 : infiltration furtive (6 gardes) rejouee en continu, pour que
tu puisses te connecter et SPECTATER quand tu veux. Chemlight bleu sur l'infiltrateur + marqueur carte
OBJECTIF + fumee verte a la reussite. Pilote par stealth_curric.pt."""
import os
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Altis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"; ND = 6
b = ArmaBridge()

SETUP = r'''
HMT_CX=20885; HMT_CY=16779;
if (!isNil "HMT_STG_GUARDS") then { { deleteVehicle _x } forEach HMT_STG_GUARDS; };
if (!isNil "HMT_STG_INF") then { if (!isNull HMT_STG_INF) then { { deleteVehicle _x } forEach attachedObjects HMT_STG_INF; deleteVehicle HMT_STG_INF } };
deleteMarker "hmt_obj";
private _mk = createMarker ["hmt_obj",[HMT_CX,HMT_CY,0]]; "hmt_obj" setMarkerType "hd_objective"; "hmt_obj" setMarkerColor "ColorGreen"; "hmt_obj" setMarkerText "OBJECTIF (infiltration)";
private _ge = createGroup east; HMT_STG_GUARDS=[]; private _nd = __ND__;
for "_i" from 0 to (_nd-1) do {
  private _ang=_i*(360/_nd); private _gx=HMT_CX+50*sin _ang; private _gy=HMT_CY+50*cos _ang;
  _ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"];
  private _u=(units _ge) select (count (units _ge)-1);
  _u setPosATL [_gx,_gy,0]; _u setDir _ang;
  { _u disableAI _x } forEach ["MOVE","PATH","FSM","TARGET","AUTOTARGET","AUTOCOMBAT","ANIM"];
  _u setBehaviour "AWARE"; _u setUnitPos "UP"; _u setCombatMode "BLUE";
  HMT_STG_GUARDS pushBack _u;
};
private _gw = createGroup west; private _ix=HMT_CX; private _iy=HMT_CY-110;
_gw createUnit ["B_Soldier_F",[_ix,_iy,0],[],0,"NONE"];
HMT_STG_INF=(units _gw) select (count (units _gw)-1);
HMT_STG_INF setPosATL [_ix,_iy,0]; HMT_STG_INF allowDamage false;
{ HMT_STG_INF disableAI _x } forEach ["AUTOTARGET","TARGET","AUTOCOMBAT","FSM","COVER","SUPPRESSION","CHECKVISIBLE"];
HMT_STG_INF enableAI "MOVE"; HMT_STG_INF enableAI "PATH"; HMT_STG_INF setBehaviour "CARELESS";
HMT_STG_INF setUnitPos "AUTO"; HMT_STG_INF forceSpeed 4; HMT_STG_INF setCombatMode "BLUE";
private _cl = "Chemlight_blue" createVehicle [0,0,0]; _cl attachTo [HMT_STG_INF,[0,0,1.3]];
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_placed",false]) then { _x setVariable ["hmt_placed",true]; _x setPosATL [HMT_CX,HMT_CY-55,0]; _x setDir 0; _x setUnitPos "UP"; _x switchMove ""; ["Altis - centre d operation. Regarde au NORD : chemlight bleu = infiltrateur, anneau de gardes."] remoteExec ["hint", _x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_SETUP guards=%1 inf=%2 players=%3", count HMT_STG_GUARDS, getPosATL HMT_STG_INF, count allPlayers];
'''.replace("__ND__", str(ND))

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
private _o=_shell+[_dmg,_tox,_toy,_tod,_ngx/_ngd,_ngy/_ngd,(_ngd/HMT_S) min 2,_nge,_expo,_det,_dmg];
diag_log format ["HARMATTAN_SOBS %1", _o];
'''

ACT_TPL = r'''
private _a=__A__; private _u=HMT_STG_INF; private _p=getPosATL _u;
if (_a < 8) then { private _ang=_a*45; _u doMove [(_p#0)+14*sin _ang,(_p#1)+14*cos _ang,0]; } else { _u doMove (getPosATL _u); };
'''

SMOKE = r'''HMT_CX=20885; HMT_CY=16779; "SmokeShellGreen" createVehicle [HMT_CX,HMT_CY,0]; diag_log "HARMATTAN_SUCCESS smoke";'''


def read_sobs(timeout=15):
    n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.5)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    for ln in reversed(lines[idx:]):
        m = re.search(r"HARMATTAN_SOBS \[([^\]]+)\]", ln)
        if m: return torch.tensor([[float(v) for v in m.group(1).split(",")]], dtype=torch.float32)
    return None


def send_act(a, timeout=15):
    b.send(ACT_TPL.replace("__A__", str(int(a))), wait=True, timeout=timeout); time.sleep(1.1)


net = Net(23, 10, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/stealth_curric.pt", map_location=DEV)); net.eval()
print("=== DEMO FURTIVITE EN BOUCLE (server14, %d gardes) — connecte-toi et spectate ===" % ND, flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(2.5)
        alert = 0; res = "timeout"
        for t in range(80):
            obs = read_sobs()
            if obs is None: break
            d = obs[0, 15].item() * 140.0; det = int(obs[0, 21].item() > 0.5)
            if det: alert += 1
            if d < 20 and alert <= 3: res = "INFILTRE INVU"; b.send(SMOKE, wait=True, timeout=10); break
            if alert > 3: res = "ALARME"; break
            with torch.no_grad(): a = int(net.a_logits(obs).argmax(-1)[0])
            send_act(a)
        print("  run %d : %s | vu=%d" % (ep, res, alert), flush=True)
        time.sleep(6.0)
    except Exception as e:
        print("  run %d ERREUR %s (retry)" % (ep, str(e)[:80]), flush=True); time.sleep(3.0)
