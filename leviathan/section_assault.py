#!/usr/bin/env python3
"""section_assault.py — LE LIEUTENANT (le grade qui manquait). Patron RECURSIF de la chaine de commandement.
  LIEUTENANT : recoit l'objectif -> le decoupe en 3 sous-objectifs (3 axes) pour ses 3 SERGENTS.
  SERGENT (x3, commander.pt) : place ses 2 elements (8 soldats) vers SON sous-objectif.
  SOLDATS (24) : LAMBS execute + orchestration composera plus tard.
Force proportionnee (24 vs ~18) = un vrai assaut de section. Meme geste a chaque grade -> scalable a capitaine/colonel."""
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
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def sergent_obs(soldats, guards, sub, t_hi, maxt=14):
    """obs 17-dim du commander.pt : 8 soldats (2 elements) + gardes, RELATIFS au sous-objectif du sergent."""
    ax = sub[0]; ay = sub[1]
    ag = [[s[0] - ax, s[1] - ay, s[2]] for s in soldats]
    gd = [[g[0] - ax, g[1] - ay] for g in guards]
    parts = []
    for k in range(2):
        al = [ag[i] for i in range(4 * k, 4 * k + 4) if ag[i][2] > 0.5]
        n = len(al)
        cx = sum(a[0] for a in al) / n if n else 0.0
        cy = sum(a[1] for a in al) / n if n else 0.0
        af = n / 4.0; cover = 0.0
        if gd and n:
            best = min(gd, key=lambda g: (g[0] - cx) ** 2 + (g[1] - cy) ** 2)
            ndx = best[0] - cx; ndy = best[1] - cy; ndd = math.hypot(ndx, ndy) + 1e-6
        else:
            ndx = ndy = 0.0; ndd = 2 * S
        parts += [cx / S, cy / S, af, cover, ndx / ndd, ndy / ndd, min(ndd / S, 2.0)]
    nalive = sum(1 for a in ag if a[2] > 0.5)
    parts += [len(gd) / NG, nalive / 8.0, t_hi / maxt]
    return torch.tensor(parts, dtype=torch.float32)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--steps", type=int, default=14); a = ap.parse_args()
    b = NativeBridge(port=5816)
    net = CNet(17, 4); net.load_state_dict(torch.load(CKC, map_location="cpu")); net.eval()
    # LIEUTENANT : 3 sous-objectifs = 3 axes lateraux convergeant sur l'objectif
    SUB = [[-45, 0], [0, 0], [45, 0]]                               # rel objectif ; les 3 sergents attaquent de 3 cotes
    print("[lieutenant] 3 sergents (commander.pt) -> section 24. Objectif [%d,%d]" % (CX, CY), flush=True)

    setup = ('[] spawn { HMT_CX=%d; HMT_CY=%d; '
             'if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR }; if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS }; '
             'private _ge=createGroup east; HMT_GUARDS=[]; '
             'for "_i" from 0 to 17 do { private _ang=_i*20; private _rr=18+(_i%%3)*8; private _gx=HMT_CX+_rr*sin _ang; private _gy=HMT_CY+_rr*cos _ang; '
             'private _g=_ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"]; _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; _g setSkill 0.5; HMT_GUARDS pushBack _g; }; '
             'HMT_FR=[]; HMT_SG=[]; '                               # 3 sergents x 2 elements = 6 groupes
             'for "_sg" from 0 to 2 do { private _ga=createGroup west; private _gb=createGroup west; HMT_SG pushBack [_ga,_gb]; '
             '  for "_i" from 0 to 7 do { private _sx=HMT_CX+(_sg-1)*55+((_i%%2)*8-4); private _sy=HMT_CY-140-_i*5; private _grp=if (_i<4) then {_ga} else {_gb}; '
             '  private _s=_grp createUnit ["B_recon_F",[_sx,_sy,0],[],0,"NONE"]; _s setPosATL [_sx,_sy,0]; _s setSkill 0.6; _s setBehaviour "AWARE"; _s setCombatMode "RED"; HMT_FR pushBack _s; }; }; '
             'sleep 3; { private _r=_x; { _x reveal [_r,3] } forEach (allUnits select {side _x==east && alive _x && _x distance _r<600}); } forEach HMT_FR; '
             '(format ["HARMATTAN_ASETUP fr=%%1 gd=%%2", count HMT_FR, count HMT_GUARDS]) call HMT_EMIT; };') % (CX, CY)
    b.query(setup, r"HARMATTAN_ASETUP fr=(\d+)", want=1, timeout=15)
    time.sleep(16)

    read_fr = ('private _o=[]; { private _p=getPosATL _x; _o pushBack [round((_p select 0)-%d), round((_p select 1)-%d), (if (alive _x) then {1} else {0})]; } forEach HMT_FR; (format ["HARMATTAN_FC %%1", _o]) call HMT_EMIT;') % (CX, CY)
    read_gd = ('private _o=[]; { if (alive _x) then { private _q=getPosATL _x; _o pushBack [round((_q select 0)-%d), round((_q select 1)-%d)]; } } forEach HMT_GUARDS; (format ["HARMATTAN_GD %%1", _o]) call HMT_EMIT;') % (CX, CY)

    def rd(sqf, tag):
        r = b.query(sqf, tag + r" (\[.*\])", want=1, timeout=10)
        try: return ast.literal_eval(r[-1].group(1)) if r else None
        except Exception: return None

    print("=== ASSAUT DE SECTION : Lieutenant -> 3 Sergents -> 24 soldats ===", flush=True)
    pen0 = None
    for t in range(a.steps):
        agents = rd(read_fr, "HARMATTAN_FC")
        if not agents or len(agents) < 24:
            time.sleep(1); continue
        guards = rd(read_gd, "HARMATTAN_GD") or []
        order_parts = []
        for sg in range(3):                                        # chaque SERGENT place ses 2 elements vers SON sous-objectif
            sol = agents[sg * 8:(sg + 1) * 8]
            sub = SUB[sg]
            obs = sergent_obs(sol, guards, sub, t)
            with torch.no_grad():
                mu, _ = net(obs); act = mu.clamp(-1, 1).view(2, 2)
            wx = CX + sub[0]; wy = CY + sub[1]
            t0 = [wx + float(act[0, 0]) * R_PLACE, wy + float(act[0, 1]) * R_PLACE]
            t1 = [wx + float(act[1, 0]) * R_PLACE, wy + float(act[1, 1]) * R_PLACE]
            order_parts.append(
                ('private _ga=(HMT_SG select %d) select 0; private _gb=(HMT_SG select %d) select 1; '
                 '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach (units _ga + units _gb); '
                 '{ deleteWaypoint _x } forEach (waypoints _ga + waypoints _gb); '
                 'private _wa=_ga addWaypoint [[%.1f,%.1f,0],0]; _wa setWaypointType "MOVE"; _wa setWaypointBehaviour "COMBAT"; _wa setWaypointCombatMode "RED"; _ga setCurrentWaypoint _wa; '
                 'private _wb=_gb addWaypoint [[%.1f,%.1f,0],0]; _wb setWaypointType "MOVE"; _wb setWaypointBehaviour "COMBAT"; _wb setWaypointCombatMode "RED"; _gb setCurrentWaypoint _wb;')
                % (sg, sg, t0[0], t0[1], t1[0], t1[1]))
        b.send(" ".join(order_parts))
        time.sleep(6.5)
        alive = [ag for ag in agents if ag[2] > 0.5]
        pen = min((math.hypot(ag[0], ag[1]) for ag in alive), default=999)
        gd_alive = len(rd(read_gd, "HARMATTAN_GD") or [])
        if pen0 is None: pen0 = pen
        print("  t=%2d | vivants=%2d/24 | gardes=%2d | +proche->objectif=%.0fm" % (t, len(alive), gd_alive, pen), flush=True)
        if pen < 25: print("  >>> OBJECTIF PRIS par la SECTION !", flush=True); break
    surv = len([x for x in (rd(read_fr, "HARMATTAN_FC") or []) if len(x) > 2 and x[2] > 0.5])
    print("=== FIN section : penetration %.0f -> %.0fm | survivants=%d/24 ===" % (pen0 or 0, pen, surv), flush=True)
    b.send("{ private _v=missionNamespace getVariable [_x,[]]; { deleteVehicle _x } forEach _v; } forEach [\"HMT_FR\",\"HMT_GUARDS\"];")


if __name__ == "__main__":
    main()
