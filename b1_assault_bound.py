"""INTEGRATION avec BOUNDING OVERWATCH (Stratis, server14). Escouade de 8, 12 gardes (durci) :
 - PHASE APPROCHE (centre>120 m) : politique FORMATION (formation_v2.pt) -> colonne puis ligne ;
 - PHASE BOUNDING (<=120 m, gardes>2) : politique BOUNDING (bounding.pt, obs 28-dim) -> appui(SUPPRIMER)+bond, nettoie la defense ;
 - PHASE FINITION (gardes<=2) : politique RESCOUSSE d6 (hostage_v1_FINAL.pt) -> recup colis, exfil.
Test LIVE du transfert sim-to-real du bounding. Action 9 = SUPPRIMER (doTarget+doFire garde le + proche)."""
import os, math
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, json, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"; CX = 5569; CY = 4683; ASSAULT_R = 120.0; SB = 200.0; MVB = 20
S = 200.0; SP = 9.0; ANCH = 7.0; MAXLEAD = 55.0; SWITCH_FRAC = 0.45
COL = torch.tensor([(0, .5), (-1, -.5), (-2, .5), (-3, -.5), (-4, .5), (-5, -.5), (-6, .5), (-7, -.5)]) * SP
LIG = torch.tensor([(0, -3.5), (0, -2.5), (0, -1.5), (0, -.5), (0, .5), (0, 1.5), (0, 2.5), (0, 3.5)]) * SP
b = ArmaBridge()

SETUP = (r'''HMT_CX=__CX__; HMT_CY=__CY__; HMT_PICKED=0;
if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR; };
if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS; };
if (!isNil "HMT_HOSTAGE") then { if (!isNull HMT_HOSTAGE) then { { deleteVehicle _x } forEach attachedObjects HMT_HOSTAGE; deleteVehicle HMT_HOSTAGE } };
HMT_EXT = [HMT_CX, HMT_CY-90, 0];
HMT_HOSTAGE = "Land_Suitcase_F" createVehicle [HMT_CX,HMT_CY,0]; HMT_HOSTAGE setPosATL [HMT_CX,HMT_CY,0];
private _cl="Chemlight_green" createVehicle [0,0,0]; _cl attachTo [HMT_HOSTAGE,[0,0,0.4]];
private _ge = createGroup east; HMT_GUARDS=[]; private _nd=12;
for "_i" from 0 to (_nd-1) do { private _ang=_i*(360/_nd); private _r=if (_i % 2 == 0) then {20} else {38}; private _gx=HMT_CX+_r*sin _ang; private _gy=HMT_CY+_r*cos _ang;
  private _g = _ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"];
  _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; HMT_GUARDS pushBack _g; };
private _gw = createGroup west; HMT_FR=[];
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-150-_i*8;
  private _s = _gw createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"];
  _s setPosATL [_sx,_sy,0]; _s allowDamage true; _s setBehaviour "CARELESS"; _s setCombatMode "BLUE";
  _s enableAI "MOVE"; _s enableAI "PATH"; _s disableAI "AUTOCOMBAT"; _s disableAI "FSM"; _s disableAI "TARGET"; _s disableAI "AUTOTARGET";
  HMT_FR pushBack _s; };
createMarker ["hmt_h",[HMT_CX,HMT_CY,0]]; "hmt_h" setMarkerType "hd_objective"; "hmt_h" setMarkerColor "ColorGreen"; "hmt_h" setMarkerText "COLIS";
createMarker ["hmt_ext",HMT_EXT]; "hmt_ext" setMarkerType "hd_objective"; "hmt_ext" setMarkerColor "ColorBlue"; "hmt_ext" setMarkerText "EXFIL";
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_p",false]) then { _x setVariable ["hmt_p",true]; _x setPosATL [HMT_CX,HMT_CY-190,0]; _x setDir 0; ["BOUNDING (Stratis). 8 bleus : approche formation -> bond/appui (SUPPRIMER) sur 12 gardes -> recup colis."] remoteExec ["hint",_x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_ASETUP fr=%1 guards=%2", count HMT_FR, count HMT_GUARDS];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

FPOS = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
{ private _p=getPosATL _x; diag_log format ["HARMATTAN_FPOS %1 %2 %3", _forEachIndex, (_p select 0)-HMT_CX, (_p select 1)-HMT_CY]; } forEach HMT_FR;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

FACT = (r'''HMT_ACT=[__ACTS__];
{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _p=getPosATL _x; private _ang=_a*45;
  if (_a < 8) then { _x doMove [(_p select 0)+14*cos _ang, (_p select 1)+14*sin _ang, 0]; } else { _x doMove (getPosATL _x); };
} forEach HMT_FR;
''')

# ===== PERC BOUNDING : obs 28-dim = base(9) + coque(13) + suffer(2 partiel) + nt ; equipe assemblee en Python =====
PERC_B = (r'''HMT_SB=__CX__*0+200; HMT_CX=__CX__; HMT_CY=__CY__;
{
  private _u=_x; private _i=_forEachIndex; private _p=getPosATL _u; private _ax=(_p select 0)-HMT_CX; private _ay=(_p select 1)-HMT_CY;
  private _alv=if (alive _u) then {1} else {0};
  private _ng=objNull; private _nd2=1e9; { if (alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_nd2) then {_nd2=_d;_ng=_x}; }; } forEach HMT_GUARDS;
  private _los=0; private _ndd=400; private _gdx=0; private _gdy=0;
  if (!isNull _ng) then { _ndd=sqrt _nd2; private _q=getPosATL _ng; _gdx=((_q select 0)-HMT_CX)-_ax; _gdy=((_q select 1)-HMT_CY)-_ay;
     private _gp=getPosASL _ng; private _aps=getPosASL _u; _los=if (terrainIntersectASL [[(_aps select 0),(_aps select 1),(_aps select 2)+0.9],[(_gp select 0),(_gp select 1),(_gp select 2)+0.9]]) then {0} else {1}; };
  private _th0=if (!isNull _ng) then { _gdy atan2 _gdx } else {0}; private _shell=[];
  for "_k" from 0 to 11 do { private _ang=_th0+_k*30; private _rdx=cos _ang; private _rdy=sin _ang; private _sv=1;
     for "_s" from 1 to 20 do { private _r=_s/20*60; private _qx=(_p select 0)+_r*_rdx; private _qy=(_p select 1)+_r*_rdy;
        if (count (nearestObjects [[_qx,_qy,(_p select 2)],["House","Wall","Rock"],3])>0) exitWith {_sv=_s/20}; };
     _shell pushBack _sv; };
  private _dmg=damage _u;
  private _nt=0; { if (alive _x) then { private _q=getPosATL _x; private _dx=(_q select 0)-(_p select 0); private _dy=(_q select 1)-(_p select 1); private _dd=sqrt(_dx*_dx+_dy*_dy);
     if (_dd<110) then { private _gp=getPosASL _x; private _l=if (terrainIntersectASL [[(_p select 0),(_p select 1),(_p select 2)+0.9],[(_gp select 0),(_gp select 1),(_gp select 2)+0.9]]) then {0} else {1}; _nt=_nt+_l; }; }; } forEach HMT_GUARDS;
  private _o=[_ax,_ay,_alv,_los,_ndd]+_shell+[_dmg,_nt];
  diag_log format ["HARMATTAN_BOBS %1 %2", _i, _o];
} forEach HMT_FR;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

# ===== ACT BOUNDING : 0-7 doMove (sin est / cos nord) ; 8 hold ; 9 SUPPRIMER (target+fire garde le + proche) =====
ACT_B = (r'''HMT_ACT=[__ACTS__];
{ private _u=_x; private _i=_forEachIndex; private _a=HMT_ACT select _i; private _p=getPosATL _u;
  if (_a < 8) then { private _ang=_a*45; _u doMove [(_p select 0)+__MVB__*sin _ang, (_p select 1)+__MVB__*cos _ang, 0]; }
  else { _u doMove (getPosATL _u);
     if (_a == 9) then { private _ng=objNull; private _nd=1e9; { if (alive _x) then { private _d=_u distance2D _x; if (_d<_nd) then {_nd=_d;_ng=_x}; }; } forEach HMT_GUARDS;
        if (!isNull _ng) then { _u doTarget _ng; _u doFire _ng; }; };
  };
} forEach HMT_FR;
diag_log format ["HARMATTAN_BSTATUS galive=%1 alive=%2", ({alive _x} count HMT_GUARDS), ({alive _x} count HMT_FR)];
''').replace("__MVB__", str(MVB))

# ===== ACT d6 (finition) : recup + exfil =====
ACT_TPL = (r'''HMT_ACT = [__ACTS__];
{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _p=getPosATL _x;
  if (_a < 8) then { private _ang=_a*45; _x doMove [(_p select 0)+22*sin _ang, (_p select 1)+22*cos _ang, 0]; } else { _x doMove (getPosATL _x); };
} forEach HMT_FR;
private _car=objNull; private _cd=1e9; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_cd) then {_cd=_d;_car=_x}; }; } forEach HMT_FR;
if (_cd < 25) then { HMT_PICKED=1; };
if (HMT_PICKED==1 && !isNull _car) then { HMT_HOSTAGE setPosATL (getPosATL _car) };
private _dex=HMT_HOSTAGE distance2D [(HMT_EXT select 0),(HMT_EXT select 1),0];
private _succ=if (HMT_PICKED==1 && _dex<25) then {1} else {0};
diag_log format ["HARMATTAN_STATUS picked=%1 succ=%2 dh=%3 dex=%4 alive=%5", HMT_PICKED, _succ, round _cd, round _dex, ({alive _x} count HMT_FR)];
''')

# ===== PERC d6 (finition, 29-dim) =====
PERC = (r'''
HMT_S = 140; HMT_CX = __CX__; HMT_CY = __CY__;
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
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

SMOKE = r'''"SmokeShellGreen" createVehicle (getPosATL HMT_HOSTAGE); diag_log "HARMATTAN_RESCUE smoke";'''
# enable TARGET pour que les agents en appui puissent TIRER (suppression)
TARGETON = r'''{ _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "AWARE"; _x setCombatMode "RED"; _x setUnitPos "AUTO" } forEach HMT_FR; diag_log "HARMATTAN_TARGETON";'''
# FIGHT : au contact, on laisse l IA de combat d Arma RESOUDRE le feu (c est elle qui tue) — la politique a fait l approche+bond
FIGHT = r'''{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; } forEach HMT_FR; diag_log "HARMATTAN_FIGHT on";'''
# RESTORE : reprend le controle (mouvement pilote) pour la finition recup+exfil
RESTORE = r'''{ _x disableAI "AUTOCOMBAT"; _x disableAI "FSM"; _x setBehaviour "AWARE"; } forEach HMT_FR; diag_log "HARMATTAN_RESTORE";'''
GSTAT = r'''diag_log format ["HARMATTAN_BSTATUS galive=%1 alive=%2", ({alive _x} count HMT_GUARDS), ({alive _x} count HMT_FR)];'''


def read_fpos(timeout=15, tries=3):
    for _ in range(tries):
        n = b.send(FPOS, wait=True, timeout=timeout); time.sleep(0.6)
        lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
        pos = {}
        for ln in lines[idx:]:
            m = re.search(r"HARMATTAN_FPOS (\d+) (-?[\d.]+) (-?[\d.]+)", ln)
            if m: pos[int(m.group(1))] = [float(m.group(2)), float(m.group(3))]
        if len(pos) == 8: return torch.tensor([pos[k] for k in sorted(pos)])
        time.sleep(0.4)
    return None


def read_bobs(prev_act, prev_dmg, timeout=15, tries=3):
    raw = {}
    for _ in range(tries):
        n = b.send(PERC_B, wait=True, timeout=timeout); time.sleep(0.7)
        lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
        raw = {}
        for ln in lines[idx:]:
            m = re.search(r"HARMATTAN_BOBS (\d+) \[([^\]]+)\]", ln)
            if m: raw[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
        if len(raw) == 8: break
        time.sleep(0.4)
    if len(raw) != 8: return None, prev_dmg
    rows = [raw[k] for k in sorted(raw)]
    nsupp = sum(1 for x in prev_act if x == 9); nalv = max(sum(1 for r in rows if r[2] > 0.5), 1); frac = nsupp / nalv
    obs = []; newdmg = []
    for i, r in enumerate(rows):
        axi, ayi, alv, los, ndd = r[0], r[1], r[2], r[3], r[4]
        shell = r[5:17]; dmg = r[17]; nt = r[18]
        base = [axi / SB, ayi / SB, -axi / SB, -ayi / SB, alv, 0.0, 0.0, los, min(ndd / SB, 2.0)]
        sh = shell + [dmg]
        suf = [min(max((dmg - prev_dmg[i]) * 5.0, 0.0), 1.0), nt / 12.0]
        bestj = -1; bd = 1e18
        for j, rj in enumerate(rows):
            if j != i and rj[2] > 0.5:
                d = (rj[0] - axi) ** 2 + (rj[1] - ayi) ** 2
                if d < bd: bd = d; bestj = j
        if bestj >= 0:
            adx = (rows[bestj][0] - axi) / SB; ady = (rows[bestj][1] - ayi) / SB
            asupp = 1.0 if prev_act[bestj] == 9 else 0.0
        else: adx = ady = asupp = 0.0
        team = [adx, ady, asupp, frac]
        obs.append(base + sh + suf + team); newdmg.append(dmg)
    return torch.tensor(obs, dtype=torch.float32), newdmg


def send_bound(acts, timeout=15):
    b.send(ACT_B.replace("__ACTS__", ",".join(str(int(a)) for a in acts)), wait=True, timeout=timeout); time.sleep(1.5)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_BSTATUS galive=(\d+) alive=(\d+)", ln)
        if m: return {"galive": int(m.group(1)), "alive": int(m.group(2))}
    return None


def read_gstat(timeout=15):
    b.send(GSTAT, wait=True, timeout=timeout); time.sleep(0.4)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_BSTATUS galive=(\d+) alive=(\d+)", ln)
        if m: return {"galive": int(m.group(1)), "alive": int(m.group(2))}
    return None


def send_assault(acts, timeout=15):
    b.send(ACT_TPL.replace("__ACTS__", ",".join(str(int(a)) for a in acts)), wait=True, timeout=timeout); time.sleep(1.5)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_STATUS picked=(\d+) succ=(\d+) dh=(-?\d+) dex=(-?\d+) alive=(\d+)", ln)
        if m: return {"picked": int(m.group(1)), "succ": int(m.group(2)), "dex": int(m.group(4)), "alive": int(m.group(5))}
    return None


def read_aobs_d6(timeout=15, tries=3):
    for _ in range(tries):
        n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.6)
        lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
        obs = {}
        for ln in lines[idx:]:
            m = re.search(r"HARMATTAN_AOBS (\d+) \[([^\]]+)\]", ln)
            if m: obs[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
        if len(obs) == 8: return torch.tensor([obs[k] for k in sorted(obs)], dtype=torch.float32)
        time.sleep(0.4)
    return None


def fobs(agents, anchor, assault):
    obj = torch.zeros(2); tmpl = LIG if assault else COL
    h = (obj - anchor); h = h / (h.norm() + 1e-6); hp = torch.tensor([-h[1], h[0]])
    slots = anchor[None] + tmpl[:, 0:1] * h[None] + tmpl[:, 1:2] * hp[None]
    sd = slots - agents; sdn = sd.norm(dim=1, keepdim=True) + 1e-6
    od = obj[None] - agents; odn = od.norm(dim=1, keepdim=True) + 1e-6
    dx = agents[:, None, 0] - agents[None, :, 0]; dy = agents[:, None, 1] - agents[None, :, 1]
    d2 = dx * dx + dy * dy + torch.eye(8) * 1e9; j = d2.argmin(1)
    tn = agents[j] - agents; tdn = tn.norm(dim=1, keepdim=True) + 1e-6
    return torch.cat([sd / sdn, (sdn / S).clamp(max=2), h[None].expand(8, 2), od / odn, (odn / S).clamp(max=2), tn / tdn, (tdn / S).clamp(max=2)], dim=1)


netF = Net(11, 9, 512, 3).to(DEV); netF.load_state_dict(torch.load("/home/younes/compose-embodiment/formation_v2.pt", map_location=DEV)); netF.eval()
netB = Net(28, 10, 512, 3).to(DEV); netB.load_state_dict(torch.load("/home/younes/compose-embodiment/bounding.pt", map_location=DEV)); netB.eval()
netA = Net(29, 10, 512, 3).to(DEV); netA.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); netA.eval()
print("=== BOUNDING LIVE sur ARMA (Stratis, 12 gardes) : approche -> BOND/APPUI -> finition ===", flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(2.5)
        agents = read_fpos()
        if agents is None: print("  [pos None]", flush=True); time.sleep(3); continue
        anchor = agents.mean(0).clone(); d0 = max(anchor.norm().item(), 1.0)
        res = "timeout"; bounding_on = False; fight_on = False; finish_on = False; galive = 12; CONTACT_R = 45; fight_steps = 0
        prev_act = [0] * 8; prev_dmg = [0.0] * 8
        for t in range(160):
            cd = agents.mean(0).norm().item()
            if not bounding_on and not fight_on and not finish_on and cd > ASSAULT_R:   # APPROCHE = formation
                h = (-anchor); h = h / (h.norm() + 1e-6); cand = anchor + ANCH * h
                if (cand - agents.mean(0)).norm() <= MAXLEAD: anchor = cand
                assault_form = anchor.norm() <= SWITCH_FRAC * d0
                with torch.no_grad(): a = netF.a_logits(fobs(agents, anchor, assault_form)).argmax(-1)
                b.send(FACT.replace("__ACTS__", ",".join(str(int(x)) for x in a.tolist())), wait=True, timeout=15); time.sleep(1.1)
                agents = read_fpos()
                if t % 5 == 0: print("  ep%d t=%2d FORMATION  centre %dm (%s)" % (ep, t, int(cd), "ligne" if assault_form else "colonne"), flush=True)
            elif galive > 2 and cd > CONTACT_R and not fight_on and not finish_on:       # BOUNDING (bond jusqu au contact)
                if not bounding_on: b.send(TARGETON, wait=True, timeout=10); bounding_on = True; time.sleep(0.4)
                obs, prev_dmg = read_bobs(prev_act, prev_dmg)
                if obs is None: agents = read_fpos(); continue
                with torch.no_grad(): a = netB.a_logits(obs).argmax(-1)
                prev_act = a.tolist(); st = send_bound(prev_act)
                if st: galive = st["galive"]
                agents = read_fpos()
                nsup = sum(1 for x in prev_act if x == 9)
                if t % 2 == 0: print("  ep%d t=%2d BOUNDING  centre %dm | appui=%d bond=%d | gardes=%d vivants=%d" % (ep, t, int(cd), nsup, 8 - nsup, galive, st["alive"] if st else -1), flush=True)
                if st and st["alive"] == 0: res = "escouade aneantie (bounding)"; break
            elif galive > 2 and not finish_on:                                          # FIREFIGHT = l IA Arma resout le feu
                if not fight_on: b.send(FIGHT, wait=True, timeout=10); fight_on = True; time.sleep(0.5)
                fight_steps += 1
                st = read_gstat(); time.sleep(2.2)
                if st: galive = st["galive"]
                print("  ep%d t=%2d FIREFIGHT (IA Arma) | gardes=%d vivants=%d" % (ep, t, galive, st["alive"] if st else -1), flush=True)
                if st and st["alive"] == 0: res = "escouade aneantie (firefight)"; break
                if fight_steps >= 24: res = "firefight non concluant (gardes %d)" % galive; break
            else:                                                                       # FINITION = recup + exfil
                if not finish_on: b.send(RESTORE, wait=True, timeout=10); finish_on = True; time.sleep(0.4); agents = read_fpos()
                obsA = read_aobs_d6()
                if obsA is None: agents = read_fpos(); continue
                with torch.no_grad(): a = torch.distributions.Categorical(logits=netA.a_logits(obsA)).sample()
                st = send_assault(a.tolist()); agents = read_fpos()
                if t % 3 == 0 and st: print("  ep%d t=%2d FINITION  %s" % (ep, t, st), flush=True)
                if st and st["succ"]:
                    res = "COLIS RECUPERE (approche->bounding->firefight->exfil)"; b.send(SMOKE, wait=True, timeout=10)
                    print(">>> ep%d : %s t=%d <<<" % (ep, res, t), flush=True); break
                if st and st["alive"] == 0: res = "escouade aneantie (finition)"; break
            if agents is None: break
        print(">>> EP %d : %s (gardes restants %d)" % (ep, res, galive), flush=True); time.sleep(7)
    except Exception as e:
        print("  ep%d ERREUR %s (retry)" % (ep, str(e)[:110]), flush=True); time.sleep(3)
