"""DEPLOIEMENT LIVE du COMMANDANT APPRIS (incrément 3) — commander.pt pilote 2 elements dans le VRAI Arma via LAMBS.
Boucle haut-niveau : lit l'etat Arma -> obs 17-dim (comme CommanderEnv) -> politique apprise -> positions cibles
des 2 elements -> waypoints (LAMBS execute le feu-et-mouvement). Mission = securiser le colis. Stratis, server14+LAMBS."""
import os
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, math, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
CX = 5569; CY = 4683; NG = 8; S = 200.0; R_PLACE = 95.0; SECURE_R = 22.0; MAXT = 14
b = ArmaBridge()


class CNet(nn.Module):                                          # identique au trainer
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)

    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


net = CNet(17, 4); net.load_state_dict(torch.load("/home/younes/compose-embodiment/commander.pt", map_location="cpu")); net.eval()

SETUP = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR; };
if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS; };
if (!isNil "HMT_HOSTAGE") then { if (!isNull HMT_HOSTAGE) then { { deleteVehicle _x } forEach attachedObjects HMT_HOSTAGE; deleteVehicle HMT_HOSTAGE } };
HMT_HOSTAGE = "Land_Suitcase_F" createVehicle [HMT_CX,HMT_CY,0]; HMT_HOSTAGE setPosATL [HMT_CX,HMT_CY,0];
private _cl="Chemlight_green" createVehicle [0,0,0]; _cl attachTo [HMT_HOSTAGE,[0,0,0.4]];
private _ge = createGroup east; HMT_GUARDS=[];
for "_i" from 0 to 7 do { private _ang=_i*45; private _gx=HMT_CX+24*sin _ang; private _gy=HMT_CY+24*cos _ang;
  private _g=_ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"]; _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; _g setSkill 0.5; HMT_GUARDS pushBack _g; };
HMT_GA = createGroup west; HMT_GB = createGroup west; HMT_FR=[];
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-120-_i*6;
  private _grp=if (_i<4) then {HMT_GA} else {HMT_GB};
  private _s=_grp createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"]; _s setPosATL [_sx,_sy,0]; _s allowDamage true; _s setSkill 0.55; _s setBehaviour "AWARE"; HMT_FR pushBack _s; };
createMarker ["hmt_h",[HMT_CX,HMT_CY,0]]; "hmt_h" setMarkerType "hd_objective"; "hmt_h" setMarkerColor "ColorGreen"; "hmt_h" setMarkerText "COLIS";
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_p",false]) then { _x setVariable ["hmt_p",true]; _x setPosATL [HMT_CX,HMT_CY-150,0]; _x setDir 0; ["COMMANDANT APPRIS (Stratis). Une politique RL place les 2 elements ; LAMBS execute."] remoteExec ["hint",_x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_ASETUP fr=%1 guards=%2 ga=%3 gb=%4", count HMT_FR, count HMT_GUARDS, count units HMT_GA, count units HMT_GB];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

FPOSC = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
{ private _p=getPosATL _x; diag_log format ["HARMATTAN_FC %1 %2 %3 %4", _forEachIndex, round((_p select 0)-HMT_CX), round((_p select 1)-HMT_CY), (if (alive _x) then {1} else {0})]; } forEach HMT_FR;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

GPOS = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
{ if (alive _x) then { private _q=getPosATL _x; diag_log format ["HARMATTAN_GUARD %1 %2 %3", _forEachIndex, round((_q select 0)-HMT_CX), round((_q select 1)-HMT_CY)]; }; } forEach HMT_GUARDS;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

# ORDRE : placer chaque element a la position cible decidee par la politique. LAMBS execute le feu-et-mouvement.
ORDERC = r'''HMT_T0=[__T0X__,__T0Y__,0]; HMT_T1=[__T1X__,__T1Y__,0];
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; } forEach HMT_FR;
{ deleteWaypoint _x } forEach (waypoints HMT_GA + waypoints HMT_GB);
private _wa=HMT_GA addWaypoint [HMT_T0,0]; _wa setWaypointType "MOVE"; _wa setWaypointSpeed "NORMAL"; _wa setWaypointBehaviour "COMBAT"; _wa setWaypointCombatMode "RED"; HMT_GA setCurrentWaypoint _wa;
private _wb=HMT_GB addWaypoint [HMT_T1,0]; _wb setWaypointType "MOVE"; _wb setWaypointSpeed "NORMAL"; _wb setWaypointBehaviour "COMBAT"; _wb setWaypointCombatMode "RED"; HMT_GB setCurrentWaypoint _wb;
diag_log "HARMATTAN_CMDC ordered";'''

GSTAT = r'''private _dmin=9999; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_dmin) then {_dmin=_d}; }; } forEach HMT_FR;
diag_log format ["HARMATTAN_GSTAT galive=%1 alive=%2 dh=%3", ({alive _x} count HMT_GUARDS), ({alive _x} count HMT_FR), round _dmin];'''


def read_agents(timeout=15):
    ms = b.query(FPOSC, r"HARMATTAN_FC (\d+) (-?\d+) (-?\d+) (\d)", want=8, timeout=timeout)
    d = {int(m.group(1)): [float(m.group(2)), float(m.group(3)), int(m.group(4))] for m in ms}
    return [d[i] for i in range(8)] if len(d) == 8 else None


def read_guards(timeout=15):
    ms = b.query(GPOS, r"HARMATTAN_GUARD (\d+) (-?\d+) (-?\d+)", want=1, timeout=timeout)
    return [[float(m.group(2)), float(m.group(3))] for m in ms]


def gstat(timeout=15):
    ms = b.query(GSTAT, r"HARMATTAN_GSTAT galive=(\d+) alive=(\d+) dh=(-?\d+)", want=1, timeout=timeout)
    if not ms: return None
    m = ms[-1]; return {"g": int(m.group(1)), "a": int(m.group(2)), "dh": int(m.group(3))}


def build_obs(agents, guards, t_hi):
    parts = []
    for k in range(2):
        al = [agents[i] for i in range(4 * k, 4 * k + 4) if agents[i][2] > 0.5]
        n = len(al)
        if n: cx = sum(a[0] for a in al) / n; cy = sum(a[1] for a in al) / n
        else: cx = cy = 0.0
        af = n / 4.0; cover = 0.0
        if guards and n:
            best = min(guards, key=lambda g: (g[0] - cx) ** 2 + (g[1] - cy) ** 2)
            ndx = best[0] - cx; ndy = best[1] - cy; ndd = math.hypot(ndx, ndy) + 1e-6
        else: ndx = ndy = 0.0; ndd = 2 * S
        parts += [cx / S, cy / S, af, cover, ndx / ndd, ndy / ndd, min(ndd / S, 2.0)]
    nalive = sum(1 for a in agents if a[2] > 0.5)
    parts += [len(guards) / NG, nalive / 8.0, t_hi / MAXT]
    return torch.tensor(parts, dtype=torch.float32)


print("=== COMMANDANT APPRIS LIVE sur ARMA (Stratis) : commander.pt place 2 elements, LAMBS execute ===", flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(3.0)
        res = "timeout"
        for t in range(MAXT):
            agents = read_agents()
            if agents is None: time.sleep(1); continue
            guards = read_guards()
            obs = build_obs(agents, guards, t)
            with torch.no_grad(): mu, _ = net(obs); a = mu.clamp(-1, 1).view(2, 2)
            t0x = CX + float(a[0, 0]) * R_PLACE; t0y = CY + float(a[0, 1]) * R_PLACE
            t1x = CX + float(a[1, 0]) * R_PLACE; t1y = CY + float(a[1, 1]) * R_PLACE
            b.send(ORDERC.replace("__T0X__", "%.1f" % t0x).replace("__T0Y__", "%.1f" % t0y).replace("__T1X__", "%.1f" % t1x).replace("__T1Y__", "%.1f" % t1y), wait=True, timeout=12)
            time.sleep(7.0)
            st = gstat()
            ga = sum(1 for a2 in agents[:4] if a2[2] > 0.5); gb = sum(1 for a2 in agents[4:] if a2[2] > 0.5)
            print("  ep%d t=%2d | cibles A(%+.0f,%+.0f) B(%+.0f,%+.0f) | gardes=%s elemA=%d elemB=%d | +proche->colis %sm"
                  % (ep, t, t0x - CX, t0y - CY, t1x - CX, t1y - CY, st["g"] if st else "?", ga, gb, st["dh"] if st else "?"), flush=True)
            if st and st["dh"] < SECURE_R: res = "OBJECTIF ATTEINT — colis securise par le commandant APPRIS"; break
            if st and st["a"] == 0: res = "escouade aneantie"; break
        print(">>> EP %d : %s" % (ep, res), flush=True); time.sleep(6)
    except Exception as e:
        print("  ep%d ERREUR %s (retry)" % (ep, str(e)[:110]), flush=True); time.sleep(3)
