"""INTEGRATION formations + assaut otage (Stratis, server14). Escouade de 8 :
 - PHASE APPROCHE (centre>70 m) : politique de FORMATION (formation_v2.pt) -> avance en colonne puis ligne ;
 - PHASE ASSAUT  (<=70 m)      : politique de RESCOUSSE d6 (hostage_v1_FINAL.pt) -> engage gardes, recup otage, exfil.
Composition de 2 briques par phase. Otage chemlight vert, 6 gardes, EXFIL, fumee verte = libere."""
import os, math
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, json, torch
LOGJSON = os.environ.get("ASSAULT_LOG", "")          # si defini : enregistre les trajectoires du 1er run reussi puis quitte
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"; CX = 5569; CY = 4683; ASSAULT_R = 120.0
S = 200.0; SP = 9.0; ANCH = 7.0; FMOVE = 14; MAXLEAD = 55.0; SWITCH_FRAC = 0.45
COL = torch.tensor([(0, .5), (-1, -.5), (-2, .5), (-3, -.5), (-4, .5), (-5, -.5), (-6, .5), (-7, -.5)]) * SP
LIG = torch.tensor([(0, -3.5), (0, -2.5), (0, -1.5), (0, -.5), (0, .5), (0, 1.5), (0, 2.5), (0, 3.5)]) * SP
b = ArmaBridge()

SETUP = (r'''
HMT_CX=__CX__; HMT_CY=__CY__; HMT_PICKED=0;
if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR; };
if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS; };
if (!isNil "HMT_HOSTAGE") then { if (!isNull HMT_HOSTAGE) then { { deleteVehicle _x } forEach attachedObjects HMT_HOSTAGE; deleteVehicle HMT_HOSTAGE } };
deleteMarker "hmt_h"; deleteMarker "hmt_ext";
HMT_EXT = [HMT_CX, HMT_CY-90, 0];
HMT_HOSTAGE = "Land_Suitcase_F" createVehicle [HMT_CX,HMT_CY,0]; HMT_HOSTAGE setPosATL [HMT_CX,HMT_CY,0];
private _cl="Chemlight_green" createVehicle [0,0,0]; _cl attachTo [HMT_HOSTAGE,[0,0,0.4]];
private _ge = createGroup east; HMT_GUARDS=[]; private _nd=12;
for "_i" from 0 to (_nd-1) do { private _ang=_i*(360/_nd); private _r=if (_i % 2 == 0) then {20} else {38}; private _gx=HMT_CX+_r*sin _ang; private _gy=HMT_CY+_r*cos _ang;
  _ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"]; private _g=(units _ge) select (count (units _ge)-1);
  _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; HMT_GUARDS pushBack _g; };
private _gw = createGroup west; HMT_FR=[];
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-150-_i*8;
  _gw createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"]; private _s=(units _gw) select (count (units _gw)-1);
  _s setPosATL [_sx,_sy,0]; _s allowDamage true;
  _s enableAI "MOVE"; _s enableAI "PATH"; { _s disableAI _x } forEach ["AUTOCOMBAT","FSM","TARGET","AUTOTARGET","COVER","SUPPRESSION","CHECKVISIBLE"]; _s setBehaviour "CARELESS"; _s forceSpeed 4; _s setUnitPos "AUTO";
  HMT_FR pushBack _s; };
createMarker ["hmt_h",[HMT_CX,HMT_CY,0]]; "hmt_h" setMarkerType "hd_objective"; "hmt_h" setMarkerColor "ColorGreen"; "hmt_h" setMarkerText "COLIS";
createMarker ["hmt_ext",HMT_EXT]; "hmt_ext" setMarkerType "hd_objective"; "hmt_ext" setMarkerColor "ColorBlue"; "hmt_ext" setMarkerText "EXFIL";
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_p",false]) then { _x setVariable ["hmt_p",true]; _x setPosATL [HMT_CX,HMT_CY-190,0]; _x setDir 0; ["Assaut en formation (Stratis). NORD : 8 bleus avancent en colonne->ligne puis assaut otage."] remoteExec ["hint",_x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_ASETUP fr=%1 guards=%2", count HMT_FR, count HMT_GUARDS];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

FPOS = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
{ private _p=getPosATL _x; diag_log format ["HARMATTAN_FPOS %1 %2 %3", _forEachIndex, (_p select 0)-HMT_CX, (_p select 1)-HMT_CY]; } forEach HMT_FR;
private _hp=getPosATL HMT_HOSTAGE; diag_log format ["HARMATTAN_PKG %1 %2", (_hp select 0)-HMT_CX, (_hp select 1)-HMT_CY];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

GPOS = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
{ private _q=getPosATL _x; diag_log format ["HARMATTAN_GUARD %1 %2 %3", _forEachIndex, (_q select 0)-HMT_CX, (_q select 1)-HMT_CY]; } forEach HMT_GUARDS;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))
_LASTPKG = [0.0, 0.0]

FACT = (r'''HMT_ACT=[__ACTS__];
{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _p=getPosATL _x; private _ang=_a*45;
  if (_a < 8) then { _x doMove [(_p select 0)+__MV__*cos _ang, (_p select 1)+__MV__*sin _ang, 0]; } else { _x doMove (getPosATL _x); };
} forEach HMT_FR;
''').replace("__MV__", str(FMOVE))

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

ACT_TPL = (r'''
HMT_ACT = [__ACTS__];
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

SMOKE = r'''"SmokeShellGreen" createVehicle (getPosATL HMT_HOSTAGE); diag_log "HARMATTAN_RESCUE smoke";'''
COMBAT = r'''{ _x setBehaviour "AWARE"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setCombatMode "YELLOW"; _x setUnitPos "AUTO" } forEach HMT_FR; diag_log "HARMATTAN_COMBAT on";'''


def read_fpos(timeout=15):
    global _LASTPKG
    n = b.send(FPOS, wait=True, timeout=timeout); time.sleep(0.5)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    pos = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_FPOS (\d+) (-?[\d.]+) (-?[\d.]+)", ln)
        if m: pos[int(m.group(1))] = [float(m.group(2)), float(m.group(3))]
        mp = re.search(r"HARMATTAN_PKG (-?[\d.]+) (-?[\d.]+)", ln)
        if mp: _LASTPKG = [float(mp.group(1)), float(mp.group(2))]
    return torch.tensor([pos[k] for k in sorted(pos)]) if len(pos) == 8 else None


def read_guards(timeout=15):
    n = b.send(GPOS, wait=True, timeout=timeout); time.sleep(0.4)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    g = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_GUARD (\d+) (-?[\d.]+) (-?[\d.]+)", ln)
        if m: g[int(m.group(1))] = [float(m.group(2)), float(m.group(3))]
    return [g[k] for k in sorted(g)]


def read_aobs(timeout=15):
    n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.6)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    obs = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_AOBS (\d+) \[([^\]]+)\]", ln)
        if m: obs[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
    return torch.tensor([obs[k] for k in sorted(obs)], dtype=torch.float32) if len(obs) == 8 else None


def send(sqf, acts, timeout=15, slp=1.1):
    b.send(sqf.replace("__ACTS__", ",".join(str(int(a)) for a in acts)), wait=True, timeout=timeout); time.sleep(slp)


def send_assault(acts, timeout=15):
    b.send(ACT_TPL.replace("__ACTS__", ",".join(str(int(a)) for a in acts)), wait=True, timeout=timeout); time.sleep(1.5)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_STATUS picked=(\d+) succ=(\d+) dh=(-?\d+) dex=(-?\d+) alive=(\d+)", ln)
        if m: return {"picked": int(m.group(1)), "succ": int(m.group(2)), "dex": int(m.group(4)), "alive": int(m.group(5))}
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
netA = Net(29, 10, 512, 3).to(DEV); netA.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); netA.eval()
print("=== ASSAUT EN FORMATION sur ARMA (Stratis) — approche formation -> assaut otage ===", flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(2.5)
        agents = read_fpos()
        if agents is None: print("  [pos None]", flush=True); time.sleep(3); continue
        guards = read_guards() if LOGJSON else []; traj = []
        anchor = agents.mean(0).clone(); d0 = max(anchor.norm().item(), 1.0); res = "timeout"; phase = "FORMATION"; combat_sent = False
        for t in range(95):
            cd = agents.mean(0).norm().item()
            if LOGJSON: traj.append({"a": [[round(x, 1), round(y, 1)] for x, y in agents.tolist()], "pkg": [round(_LASTPKG[0], 1), round(_LASTPKG[1], 1)], "ph": "ASSAULT" if combat_sent else "FORM"})
            if cd > ASSAULT_R and not combat_sent:                          # PHASE APPROCHE = formation (verrou : une fois en assaut, on y reste)
                phase = "FORMATION"
                h = (-anchor); h = h / (h.norm() + 1e-6); cand = anchor + ANCH * h
                if (cand - agents.mean(0)).norm() <= MAXLEAD: anchor = cand
                assault_form = anchor.norm() <= SWITCH_FRAC * d0
                with torch.no_grad(): a = netF.a_logits(fobs(agents, anchor, assault_form)).argmax(-1)
                send(FACT, a.tolist(), slp=1.1)
                agents = read_fpos()
                if t % 6 == 0: print("  ep%d t=%2d FORMATION centre->otage %dm (%s)" % (ep, t, int(cd), "ligne" if assault_form else "colonne"), flush=True)
            else:                                                          # PHASE ASSAUT = rescousse d6
                phase = "ASSAUT"
                if not combat_sent: b.send(COMBAT, wait=True, timeout=10); combat_sent = True; time.sleep(0.4)
                obs = read_aobs()
                if obs is None: agents = read_fpos(); continue
                with torch.no_grad(): a = torch.distributions.Categorical(logits=netA.a_logits(obs)).sample()
                st = send_assault(a.tolist())
                agents = read_fpos()
                if t % 4 == 0 and st: print("  ep%d t=%2d ASSAUT %s" % (ep, t, st), flush=True)
                if st and st["succ"]:
                    res = "OTAGE LIBERE (assaut en formation)"; b.send(SMOKE, wait=True, timeout=10); print(">>> ep%d : %s t=%d <<<" % (ep, res, t), flush=True)
                    if LOGJSON:
                        traj.append({"a": [[round(x, 1), round(y, 1)] for x, y in agents.tolist()], "pkg": [round(_LASTPKG[0], 1), round(_LASTPKG[1], 1)], "ph": "ASSAULT"})
                        json.dump({"S": S, "ext": [0, -90], "assault_r": ASSAULT_R, "guards": guards, "steps": traj}, open(LOGJSON, "w"))
                        print("LOG ECRIT -> %s (%d pas, %d gardes)" % (LOGJSON, len(traj), len(guards)), flush=True); sys.exit(0)
                    break
                if st and st["alive"] == 0: res = "escouade aneantie"; break
            if agents is None: break
        print(">>> EP %d : %s" % (ep, res), flush=True); time.sleep(7)
    except Exception as e:
        print("  ep%d ERREUR %s (retry)" % (ep, str(e)[:90]), flush=True); time.sleep(3)
