#!/usr/bin/env python3
"""assault_commander.py — LE SOUS-OFFICIER AU MILIEU. Le commandant appris (commander.pt) coordonne
l'assaut d'un FOB : il place 2 elements (escouades de 4) vers l'objectif, LAMBS execute le feu-et-mouvement.
= l'etage 'comment gagner' qui manquait. On mesure la penetration (le commandant fait-il progresser l'assaut ?)."""
import sys, time, ast, math, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import FOBS
import torch, torch.nn as nn

CKPT = "/home/younes/compose-embodiment/commander.pt"
S = 200.0; R_PLACE = 95.0; NG = 8; MAXT = 14


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def build_obs(agents, guards, t_hi):
    parts = []
    for k in range(2):
        al = [agents[i] for i in range(4 * k, 4 * k + 4) if agents[i][2] > 0.5]
        n = len(al)
        cx = sum(a[0] for a in al) / n if n else 0.0
        cy = sum(a[1] for a in al) / n if n else 0.0
        af = n / 4.0; cover = 0.0
        if guards and n:
            best = min(guards, key=lambda g: (g[0] - cx) ** 2 + (g[1] - cy) ** 2)
            ndx = best[0] - cx; ndy = best[1] - cy; ndd = math.hypot(ndx, ndy) + 1e-6
        else:
            ndx = ndy = 0.0; ndd = 2 * S
        parts += [cx / S, cy / S, af, cover, ndx / ndd, ndy / ndd, min(ndd / S, 2.0)]
    nalive = sum(1 for a in agents if a[2] > 0.5)
    parts += [len(guards) / NG, nalive / 8.0, t_hi / MAXT]
    return torch.tensor(parts, dtype=torch.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fob", default="M1")
    ap.add_argument("--steps", type=int, default=12)
    a = ap.parse_args()
    b = NativeBridge(port=5816)
    CX, CY = [4279, 3560]                                          # objectif OUVERT (combat loyal), pas le FOB fortifie
    net = CNet(17, 4); net.load_state_dict(torch.load(CKPT, map_location="cpu")); net.eval()
    print("[commandant] commander.pt charge (obs17/act4). Objectif OUVERT [%d,%d] + 8 gardes" % (CX, CY), flush=True)

    setup = ('[] spawn { HMT_CX=%d; HMT_CY=%d; '
             'if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR }; '
             'if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS }; '
             'private _ge=createGroup east; HMT_GUARDS=[]; '
             'for "_i" from 0 to 7 do { private _ang=_i*45; private _gx=HMT_CX+24*sin _ang; private _gy=HMT_CY+24*cos _ang; '
             'private _g=_ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"]; _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; _g setSkill 0.5; HMT_GUARDS pushBack _g; }; '
             'HMT_GA=createGroup west; HMT_GB=createGroup west; HMT_FR=[]; '
             'for "_i" from 0 to 7 do { private _sx=HMT_CX + ((_i%%2)*8-4); private _sy=HMT_CY-130-_i*5; '
             'private _grp=if (_i<4) then {HMT_GA} else {HMT_GB}; '
             'private _s=_grp createUnit ["B_recon_F",[_sx,_sy,0],[],0,"NONE"]; _s setPosATL [_sx,_sy,0]; '
             '_s setSkill 0.6; _s setBehaviour "AWARE"; _s setCombatMode "RED"; _s addMagazine "SmokeShell"; HMT_FR pushBack _s; }; '
             'sleep 3; { private _r=_x; { _x reveal [_r,3] } forEach (allUnits select {side _x==east && alive _x && _x distance _r<500}); } forEach HMT_FR; '
             '(format ["HARMATTAN_ASETUP fr=%%1", count HMT_FR]) call HMT_EMIT; };') % (CX, CY)
    b.query(setup, r"HARMATTAN_ASETUP fr=(\d+)", want=1, timeout=15)
    time.sleep(16)

    read_fr = ('private _o=[]; { private _p=getPosATL _x; _o pushBack [round((_p select 0)-%d), round((_p select 1)-%d), (if (alive _x) then {1} else {0})]; } forEach HMT_FR; '
               '(format ["HARMATTAN_FC %%1", _o]) call HMT_EMIT;') % (CX, CY)
    read_gd = ('private _o=[]; { if (alive _x) then { private _q=getPosATL _x; _o pushBack [round((_q select 0)-%d), round((_q select 1)-%d)]; } } forEach HMT_GUARDS; '
               '(format ["HARMATTAN_GD %%1", _o]) call HMT_EMIT;') % (CX, CY)

    def rd(sqf, tag):
        r = b.query(sqf, tag + r" (\[.*\])", want=1, timeout=10)
        try:
            return ast.literal_eval(r[-1].group(1)) if r else None
        except Exception:
            return None

    print("=== ASSAUT COORDONNE PAR LE COMMANDANT (2 elements vers %s) ===" % a.fob, flush=True)
    pen_start = None
    for t in range(a.steps):
        agents = rd(read_fr, "HARMATTAN_FC")
        if not agents or len(agents) < 8:
            time.sleep(1); continue
        guards = rd(read_gd, "HARMATTAN_GD") or []
        obs = build_obs(agents, guards, t)
        with torch.no_grad():
            mu, _ = net(obs); act = mu.clamp(-1, 1).view(2, 2)
        t0 = [CX + float(act[0, 0]) * R_PLACE, CY + float(act[0, 1]) * R_PLACE]
        t1 = [CX + float(act[1, 0]) * R_PLACE, CY + float(act[1, 1]) * R_PLACE]
        order = ('HMT_T0=[%.1f,%.1f,0]; HMT_T1=[%.1f,%.1f,0]; '
                 '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach HMT_FR; '
                 '{ deleteWaypoint _x } forEach (waypoints HMT_GA + waypoints HMT_GB); '
                 'private _wa=HMT_GA addWaypoint [HMT_T0,0]; _wa setWaypointType "MOVE"; _wa setWaypointSpeed "NORMAL"; _wa setWaypointBehaviour "COMBAT"; _wa setWaypointCombatMode "RED"; HMT_GA setCurrentWaypoint _wa; '
                 'private _wb=HMT_GB addWaypoint [HMT_T1,0]; _wb setWaypointType "MOVE"; _wb setWaypointSpeed "NORMAL"; _wb setWaypointBehaviour "COMBAT"; _wb setWaypointCombatMode "RED"; HMT_GB setCurrentWaypoint _wb;') % (t0[0], t0[1], t1[0], t1[1])
        b.send(order)
        time.sleep(6.5)
        alive = [ag for ag in agents if ag[2] > 0.5]
        pen = min((math.hypot(ag[0], ag[1]) for ag in alive), default=999)
        if pen_start is None: pen_start = pen
        print("  t=%2d | cibles A(%+.0f,%+.0f) B(%+.0f,%+.0f) | vivants=%d | +proche->FOB=%.0fm"
              % (t, t0[0]-CX, t0[1]-CY, t1[0]-CX, t1[1]-CY, len(alive), pen), flush=True)
        if pen < 30: print("  >>> FOB ATTEINT par l'assaut coordonne !", flush=True); break
    print("=== FIN : penetration %.0fm -> %.0fm ===" % (pen_start or 0, pen), flush=True)
    b.send("if (!isNil \"HMT_FR\") then { { deleteVehicle _x } forEach HMT_FR; HMT_FR=[]; };")


if __name__ == "__main__":
    main()
