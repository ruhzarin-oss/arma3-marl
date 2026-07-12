"""FORMATIONS V2 EN ARMA (Stratis, server14). Escouade de 8 : avance vers l'objectif en COLONNE puis BASCULE
en LIGNE pres de l'objectif. La logique (ancre qui avance, slots tournes selon le cap, transition) tourne
en Python (= l'env d'entrainement) ; Arma donne les positions et execute les doMove. Politique = formation_v2.pt."""
import os, math
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"; CX = 2450; CY = 5550; S = 200.0; SP = 9.0; ANCH = 7.0; MOVE = 14; MAXLEAD = 55.0; SWITCH_FRAC = 0.45; REACH = 18.0
COL = [(0, .5), (-1, -.5), (-2, .5), (-3, -.5), (-4, .5), (-5, -.5), (-6, .5), (-7, -.5)]      # colonne (approche)
LIG = [(0, -3.5), (0, -2.5), (0, -1.5), (0, -.5), (0, .5), (0, 1.5), (0, 2.5), (0, 3.5)]       # ligne (assaut)
COL = torch.tensor(COL) * SP; LIG = torch.tensor(LIG) * SP
b = ArmaBridge()

SETUP = (r'''
HMT_CX=__CX__; HMT_CY=__CY__;
if (!isNil "HMT_SQUAD") then { { deleteVehicle _x } forEach HMT_SQUAD; };
deleteMarker "hmt_obj";
createMarker ["hmt_obj",[HMT_CX,HMT_CY,0]]; "hmt_obj" setMarkerType "hd_objective"; "hmt_obj" setMarkerColor "ColorGreen"; "hmt_obj" setMarkerText "OBJECTIF";
private _gw = createGroup west; HMT_SQUAD=[];
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-150-_i*8;
  _gw createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"]; private _s=(units _gw) select (count (units _gw)-1);
  _s setPosATL [_sx,_sy,0]; _s allowDamage false;
  { _s disableAI _x } forEach ["AUTOTARGET","TARGET","AUTOCOMBAT","FSM","COVER","SUPPRESSION","CHECKVISIBLE"];
  _s enableAI "MOVE"; _s enableAI "PATH"; _s setBehaviour "CARELESS"; _s setUnitPos "AUTO"; _s forceSpeed 4; _s setCombatMode "BLUE";
  HMT_SQUAD pushBack _s; };
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_p",false]) then { _x setVariable ["hmt_p",true]; _x setPosATL [HMT_CX,HMT_CY-185,0]; _x setDir 0; ["Formations (Stratis). Regarde au NORD : 8 bleus en colonne, bascule en ligne pres de l objectif."] remoteExec ["hint",_x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_FSETUP n=%1", count HMT_SQUAD];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

PERC = (r'''
HMT_CX=__CX__; HMT_CY=__CY__;
{ private _p=getPosATL _x; diag_log format ["HARMATTAN_FPOS %1 %2 %3", _forEachIndex, (_p select 0)-HMT_CX, (_p select 1)-HMT_CY]; } forEach HMT_SQUAD;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

ACT_TPL = (r'''
HMT_CX=__CX__; HMT_CY=__CY__; HMT_ACT=[__ACTS__];
{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _p=getPosATL _x; private _ang=_a*45;
  if (_a < 8) then { _x doMove [(_p select 0)+__MV__*cos _ang, (_p select 1)+__MV__*sin _ang, 0]; } else { _x doMove (getPosATL _x); };
} forEach HMT_SQUAD;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY)).replace("__MV__", str(MOVE))


def read_fpos(timeout=15):
    n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.5)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    pos = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_FPOS (\d+) (-?[\d.]+) (-?[\d.]+)", ln)
        if m: pos[int(m.group(1))] = [float(m.group(2)), float(m.group(3))]
    return torch.tensor([pos[k] for k in sorted(pos)]) if len(pos) == 8 else None


def send_act(acts, timeout=15):
    b.send(ACT_TPL.replace("__ACTS__", ",".join(str(int(a)) for a in acts)), wait=True, timeout=timeout); time.sleep(1.1)


def obs_from(agents, anchor, assault):
    obj = torch.zeros(2)
    tmpl = LIG if assault else COL
    h = (obj - anchor); h = h / (h.norm() + 1e-6); hp = torch.tensor([-h[1], h[0]])
    slots = anchor[None] + tmpl[:, 0:1] * h[None] + tmpl[:, 1:2] * hp[None]
    sd = slots - agents; sdn = sd.norm(dim=1, keepdim=True) + 1e-6
    od = obj[None] - agents; odn = od.norm(dim=1, keepdim=True) + 1e-6
    dx = agents[:, None, 0] - agents[None, :, 0]; dy = agents[:, None, 1] - agents[None, :, 1]
    d2 = dx * dx + dy * dy + torch.eye(8) * 1e9; j = d2.argmin(1)
    tn = agents[j] - agents; tdn = tn.norm(dim=1, keepdim=True) + 1e-6
    o = torch.cat([sd / sdn, (sdn / S).clamp(max=2), h[None].expand(8, 2), od / odn, (odn / S).clamp(max=2), tn / tdn, (tdn / S).clamp(max=2)], dim=1)
    return o


net = Net(11, 9, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/formation_v2.pt", map_location=DEV)); net.eval()
print("=== FORMATIONS V2 EN BOUCLE sur ARMA (Stratis) — colonne -> bascule -> ligne ===", flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(2.5)
        agents = read_fpos()
        if agents is None: print("  [pos None]", flush=True); time.sleep(3); continue
        anchor = agents.mean(0).clone(); d0 = anchor.norm().item(); res = "timeout"
        for t in range(60):
            cent = agents.mean(0)
            h = (-anchor); h = h / (h.norm() + 1e-6)
            cand = anchor + ANCH * h
            if (cand - cent).norm() <= MAXLEAD and anchor.norm() > REACH: anchor = cand
            assault = anchor.norm() <= SWITCH_FRAC * d0
            obs = obs_from(agents, anchor, assault)
            with torch.no_grad(): a = net.a_logits(obs).argmax(-1)
            if t % 6 == 0: print("  ep%d t=%2d | centre->obj %3dm | %s | ancre %3dm" % (ep, t, int(cent.norm()), "LIGNE(assaut)" if assault else "colonne", int(anchor.norm())), flush=True)
            send_act(a.tolist())
            agents = read_fpos()
            if agents is None: break
            if agents.mean(0).norm() < 22: res = "OBJECTIF ATTEINT EN FORMATION"; print(">>> ep%d : %s t=%d <<<" % (ep, res, t), flush=True); break
        print(">>> EP %d : %s" % (ep, res), flush=True); time.sleep(7)
    except Exception as e:
        print("  ep%d ERREUR %s (retry)" % (ep, str(e)[:80]), flush=True); time.sleep(3)
