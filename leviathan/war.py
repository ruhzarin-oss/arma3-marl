#!/usr/bin/env python3
"""war.py — BLOC 2 : la SYMETRIE. Les DEUX camps ont leur chaine de commandement (commander.pt).
  ATTAQUANT (west) : commandant -> assaille l'objectif.
  DEFENSEUR (east) : commandant -> CONTRE-ATTAQUE (objectif = centre de gravite de l'ennemi = defendre en reagissant).
Deux commandements symetriques qui s'affrontent sur le vrai Arma. Socle de la co-evolution (bloc 3)."""
import sys, time, ast, math, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch, torch.nn as nn

CKC = "/home/younes/compose-embodiment/commander.pt"
CX, CY = 4279, 3560
S = 200.0; R_PLACE = 95.0; NG = 8


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1); self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def cobs(sol, foes, obj, t, maxt=14):
    """obs 17-dim : 8 soldats (2 elements) + ennemis, RELATIFS a l'objectif du camp."""
    ax, ay = obj; ag = [[s[0] - ax, s[1] - ay, s[2]] for s in sol]; gd = [[g[0] - ax, g[1] - ay] for g in foes]
    parts = []
    for k in range(2):
        al = [ag[i] for i in range(4 * k, 4 * k + 4) if ag[i][2] > 0.5]; n = len(al)
        cx = sum(a[0] for a in al) / n if n else 0.0; cy = sum(a[1] for a in al) / n if n else 0.0
        if gd and n:
            bg = min(gd, key=lambda g: (g[0] - cx) ** 2 + (g[1] - cy) ** 2); ndx = bg[0] - cx; ndy = bg[1] - cy; ndd = math.hypot(ndx, ndy) + 1e-6
        else:
            ndx = ndy = 0.0; ndd = 2 * S
        parts += [cx / S, cy / S, n / 4.0, 0.0, ndx / ndd, ndy / ndd, min(ndd / S, 2.0)]
    parts += [len(gd) / NG, sum(1 for a in ag if a[2] > 0.5) / 8.0, t / maxt]
    return torch.tensor(parts, dtype=torch.float32)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--steps", type=int, default=16); a = ap.parse_args()
    b = NativeBridge(port=5816)
    net = CNet(17, 4); net.load_state_dict(torch.load(CKC, map_location="cpu")); net.eval()
    print("[GUERRE] 2 commandements symetriques (commander.pt). Attaquant west vs Defenseur east. Objectif [%d,%d]" % (CX, CY), flush=True)

    setup = ('[] spawn { HMT_CX=%d; HMT_CY=%d; { if (!isNil _x) then { { deleteVehicle _y } forEach (missionNamespace getVariable [_x,[]]) } } forEach ["HMT_ATK_FR","HMT_DEF_FR"]; '
             'HMT_ATK_FR=[]; HMT_ATK_SG=[]; HMT_DEF_FR=[]; HMT_DEF_SG=[]; '
             'for "_sg" from 0 to 1 do { private _ga=createGroup west; private _gb=createGroup west; HMT_ATK_SG pushBack [_ga,_gb]; private _lat=(_sg*2-1)*40; '
             '  for "_i" from 0 to 7 do { private _grp=if (_i<4) then {_ga} else {_gb}; private _s=_grp createUnit ["B_recon_F",[HMT_CX+_lat,HMT_CY-150-_i*4,0],[],0,"NONE"]; _s setPosATL [HMT_CX+_lat+(_i%%2)*4,HMT_CY-150-_i*4,0]; _s setSkill 0.55; _s setBehaviour "AWARE"; _s setCombatMode "RED"; HMT_ATK_FR pushBack _s; }; }; '
             'for "_sg" from 0 to 1 do { private _ga=createGroup east; private _gb=createGroup east; HMT_DEF_SG pushBack [_ga,_gb]; private _lat=(_sg*2-1)*30; '
             '  for "_i" from 0 to 7 do { private _grp=if (_i<4) then {_ga} else {_gb}; private _s=_grp createUnit ["O_Soldier_F",[HMT_CX+_lat,HMT_CY+15+_i*3,0],[],0,"NONE"]; _s setPosATL [HMT_CX+_lat+(_i%%2)*4,HMT_CY+15+_i*3,0]; _s setSkill 0.55; _s setBehaviour "AWARE"; _s setCombatMode "RED"; HMT_DEF_FR pushBack _s; }; }; '
             'sleep 3; { private _r=_x; { _x reveal [_r,2.5] } forEach HMT_DEF_FR } forEach HMT_ATK_FR; { private _r=_x; { _x reveal [_r,2.5] } forEach HMT_ATK_FR } forEach HMT_DEF_FR; '
             '(format ["HARMATTAN_ASETUP atk=%%1 def=%%2", count HMT_ATK_FR, count HMT_DEF_FR]) call HMT_EMIT; };') % (CX, CY)
    sr = b.query(setup, r"HARMATTAN_ASETUP atk=(\d+) def=(\d+)", want=1, timeout=25)
    print("[setup] atk=%s def=%s" % ((sr[-1].group(1), sr[-1].group(2)) if sr else ("?", "?")), flush=True)
    time.sleep(16)

    def read(var):
        sqf = ('private _o=[]; { private _p=getPosATL _x; _o pushBack [round((_p select 0)-%d), round((_p select 1)-%d), (if (alive _x) then {1} else {0})]; } forEach %s; (format ["HARMATTAN_RD %%1", _o]) call HMT_EMIT;') % (CX, CY, var)
        r = b.query(sqf, r"HARMATTAN_RD (\[.*\])", want=1, timeout=10)
        try: return ast.literal_eval(r[-1].group(1)) if r else None
        except Exception: return None

    def drive(sgvar, sol, foes, obj, t):
        parts = []
        for sg in range(2):
            s8 = sol[sg * 8:(sg + 1) * 8]
            if len(s8) < 8: continue
            with torch.no_grad():
                mu, _ = net(cobs(s8, foes, obj, t)); act = mu.clamp(-1, 1).view(2, 2)
            wx, wy = CX + obj[0], CY + obj[1]
            t0 = [wx + float(act[0, 0]) * R_PLACE, wy + float(act[0, 1]) * R_PLACE]; t1 = [wx + float(act[1, 0]) * R_PLACE, wy + float(act[1, 1]) * R_PLACE]
            parts.append(('private _ga=(%s select %d) select 0; private _gb=(%s select %d) select 1; { _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach (units _ga+units _gb); '
                          '{ deleteWaypoint _x } forEach (waypoints _ga+waypoints _gb); private _wa=_ga addWaypoint [[%.1f,%.1f,0],0]; _wa setWaypointType "MOVE"; _wa setWaypointCombatMode "RED"; _ga setCurrentWaypoint _wa; '
                          'private _wb=_gb addWaypoint [[%.1f,%.1f,0],0]; _wb setWaypointType "MOVE"; _wb setWaypointCombatMode "RED"; _gb setCurrentWaypoint _wb;') % (sgvar, sg, sgvar, sg, t0[0], t0[1], t1[0], t1[1]))
        if parts: b.send(" ".join(parts))

    def centroid(units):
        al = [u for u in units if u[2] > 0.5]
        if not al: return [0, 0]
        return [sum(u[0] for u in al) / len(al), sum(u[1] for u in al) / len(al)]

    print("=== GUERRE : Attaquant (assaut objectif) vs Defenseur (contre-attaque) ===", flush=True)
    for t in range(a.steps):
        atk = read("HMT_ATK_FR"); dfn = read("HMT_DEF_FR")
        if not atk or not dfn: time.sleep(1); continue
        drive("HMT_ATK_SG", atk, dfn, [0, 0], t)                    # attaquant -> l'objectif (0,0)
        drive("HMT_DEF_SG", dfn, atk, centroid(atk), t)             # defenseur -> le centre de gravite ennemi (contre-attaque)
        time.sleep(6.0)
        na = sum(1 for u in atk if u[2] > 0.5); nd = sum(1 for u in dfn if u[2] > 0.5)
        pen = min((math.hypot(u[0], u[1]) for u in atk if u[2] > 0.5), default=999)
        print("  t=%2d | ATTAQUANT %2d/16 (->obj %.0fm) | DEFENSEUR %2d/16" % (t, na, pen, nd), flush=True)
        if na == 0 or nd == 0: break
    print("=== FIN GUERRE : attaquant %d/16, defenseur %d/16, penetration %.0fm ===" % (na, nd, pen), flush=True)
    b.send("{ if (!isNil _x) then { { deleteVehicle _y } forEach (missionNamespace getVariable [_x,[]]) } } forEach [\"HMT_ATK_FR\",\"HMT_DEF_FR\"];")


if __name__ == "__main__":
    main()
