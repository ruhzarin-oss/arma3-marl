#!/usr/bin/env python3
"""army.py — LA CHAINE DE COMMANDEMENT COMPLETE, moteur RECURSIF (finit tous les grades d'un coup).
Chaque officier decoupe son objectif en sous-objectifs (eventail) pour ses N subordonnes ; recursion jusqu'aux
SERGENTS (commander.pt, 8 soldats chacun). BRANCH=[3,3] => Capitaine(3 Lt(3 Sgt(8))) = 72. BRANCH=[3] => Lt(24).
Teste au niveau CAPITAINE (72) contre un VRAI FOB. Meme patron => scalable Colonel/General."""
import sys, time, ast, math, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import FOBS
import torch, torch.nn as nn

CKC = "/home/younes/compose-embodiment/commander.pt"
S = 200.0; R_PLACE = 95.0; NG = 8


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def fan(obj, n, width):
    """officier : place n sous-objectifs en eventail (largeur width, lateral X) centres sur obj."""
    if n <= 1:
        return [list(obj)]
    return [[obj[0] + width * (i / (n - 1) - 0.5), obj[1]] for i in range(n)]


def allocate(obj, branch, widths, depth=0):
    """recursion : de l'objectif du capitaine -> la liste des objectifs de SERGENTS (feuilles)."""
    if depth >= len(branch):
        return [list(obj)]
    out = []
    for s in fan(obj, branch[depth], widths[depth]):
        out += allocate(s, branch, widths, depth + 1)
    return out


def sergent_obs(soldats, guards, sub, t_hi, maxt=14):
    ax, ay = sub[0], sub[1]
    ag = [[s[0] - ax, s[1] - ay, s[2]] for s in soldats]
    gd = [[g[0] - ax, g[1] - ay] for g in guards]
    parts = []
    for k in range(2):
        al = [ag[i] for i in range(4 * k, 4 * k + 4) if ag[i][2] > 0.5]
        n = len(al)
        cx = sum(a[0] for a in al) / n if n else 0.0
        cy = sum(a[1] for a in al) / n if n else 0.0
        af = n / 4.0
        if gd and n:
            best = min(gd, key=lambda g: (g[0] - cx) ** 2 + (g[1] - cy) ** 2)
            ndx = best[0] - cx; ndy = best[1] - cy; ndd = math.hypot(ndx, ndy) + 1e-6
        else:
            ndx = ndy = 0.0; ndd = 2 * S
        parts += [cx / S, cy / S, af, 0.0, ndx / ndd, ndy / ndd, min(ndd / S, 2.0)]
    parts += [len(gd) / NG, sum(1 for a in ag if a[2] > 0.5) / 8.0, t_hi / maxt]
    return torch.tensor(parts, dtype=torch.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fob", default="M1"); ap.add_argument("--steps", type=int, default=16)
    ap.add_argument("--branch", default="3,3")                      # Capitaine(3 Lt(3 Sgt)) = 72 ; "3" => section 24
    a = ap.parse_args()
    branch = [int(x) for x in a.branch.split(",")]
    widths = [150, 55, 25][:len(branch)]
    nS = 1
    for x in branch: nS *= x                                        # nb de sergents (feuilles)
    nTot = nS * 8
    b = NativeBridge(port=5816)
    net = CNet(17, 4); net.load_state_dict(torch.load(CKC, map_location="cpu")); net.eval()
    fob = next(([f[1], f[2]] for f in FOBS if f[0] == a.fob), [4279, 3856]); CX, CY = fob
    grades = {1: "Sergent", 2: "Lieutenant", 3: "Capitaine", 4: "Colonel"}.get(len(branch) + 1, "Officier")
    print("[%s] branch=%s -> %d sergents / %d soldats vs FOB %s %s" % (grades, branch, nS, nTot, a.fob, fob), flush=True)

    setup = ('[] spawn { HMT_CX=%d; HMT_CY=%d; if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR }; '
             'HMT_FR=[]; HMT_SG=[]; private _ns=%d; '
             'for "_sg" from 0 to (_ns-1) do { private _ga=createGroup west; private _gb=createGroup west; HMT_SG pushBack [_ga,_gb]; '
             '  private _lat=((_sg/(_ns-1))-0.5)*260; '
             '  for "_i" from 0 to 7 do { private _sx=HMT_CX+_lat+((_i%%2)*8-4); private _sy=HMT_CY-170-(_i*5); private _grp=if (_i<4) then {_ga} else {_gb}; '
             '  private _s=_grp createUnit ["B_recon_F",[_sx,_sy,0],[],0,"NONE"]; _s setPosATL [_sx,_sy,0]; _s setSkill 0.6; _s setBehaviour "AWARE"; _s setCombatMode "RED"; HMT_FR pushBack _s; }; }; '
             'sleep 3; { private _r=_x; { _x reveal [_r,3] } forEach (allUnits select {side _x==east && alive _x && _x distance _r<700}); } forEach HMT_FR; '
             '(format ["HARMATTAN_ASETUP fr=%%1", count HMT_FR]) call HMT_EMIT; };') % (CX, CY, nS)
    b.query(setup, r"HARMATTAN_ASETUP fr=(\d+)", want=1, timeout=20)
    time.sleep(17)

    read_fr = ('private _o=[]; { private _p=getPosATL _x; _o pushBack [round((_p select 0)-%d), round((_p select 1)-%d), (if (alive _x) then {1} else {0})]; } forEach HMT_FR; (format ["HARMATTAN_FC %%1", _o]) call HMT_EMIT;') % (CX, CY)
    read_gd = ('private _o=[]; { if (alive _x && (_x distance [%d,%d,0])<230) then { private _q=getPosATL _x; _o pushBack [round((_q select 0)-%d), round((_q select 1)-%d)]; } } forEach (allUnits select {side _x==east}); (format ["HARMATTAN_GD %%1", _o]) call HMT_EMIT;') % (CX, CY, CX, CY)

    def rd(sqf, tag):
        r = b.query(sqf, tag + r" (\[.*\])", want=1, timeout=12)
        try: return ast.literal_eval(r[-1].group(1)) if r else None
        except Exception: return None

    print("=== ASSAUT %s : recursion %s -> %d sergents (commander.pt) ===" % (grades.upper(), branch, nS), flush=True)
    pen0 = gd0 = None
    for t in range(a.steps):
        agents = rd(read_fr, "HARMATTAN_FC")
        if not agents or len(agents) < nS * 8:
            time.sleep(1); continue
        guards = rd(read_gd, "HARMATTAN_GD") or []
        if gd0 is None: gd0 = len(guards)
        subs = allocate([0, 0], branch, widths)                    # objectifs des sergents (eventail recursif)
        parts = []
        for sg in range(nS):
            sol = agents[sg * 8:(sg + 1) * 8]; sub = subs[sg]
            with torch.no_grad():
                mu, _ = net(sergent_obs(sol, guards, sub, t)); act = mu.clamp(-1, 1).view(2, 2)
            wx, wy = CX + sub[0], CY + sub[1]
            t0 = [wx + float(act[0, 0]) * R_PLACE, wy + float(act[0, 1]) * R_PLACE]
            t1 = [wx + float(act[1, 0]) * R_PLACE, wy + float(act[1, 1]) * R_PLACE]
            parts.append(('private _ga=(HMT_SG select %d) select 0; private _gb=(HMT_SG select %d) select 1; '
                          '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach (units _ga + units _gb); '
                          '{ deleteWaypoint _x } forEach (waypoints _ga + waypoints _gb); '
                          'private _wa=_ga addWaypoint [[%.1f,%.1f,0],0]; _wa setWaypointType "MOVE"; _wa setWaypointCombatMode "RED"; _ga setCurrentWaypoint _wa; '
                          'private _wb=_gb addWaypoint [[%.1f,%.1f,0],0]; _wb setWaypointType "MOVE"; _wb setWaypointCombatMode "RED"; _gb setCurrentWaypoint _wb;')
                         % (sg, sg, t0[0], t0[1], t1[0], t1[1]))
        # envoi par lots (18 groupes) pour ne pas surcharger un seul cmd
        for i in range(0, len(parts), 3):
            b.send(" ".join(parts[i:i + 3])); time.sleep(0.15)
        time.sleep(6.0)
        alive = [ag for ag in agents if ag[2] > 0.5]
        pen = min((math.hypot(ag[0], ag[1]) for ag in alive), default=999)
        gda = len(rd(read_gd, "HARMATTAN_GD") or [])
        if pen0 is None: pen0 = pen
        print("  t=%2d | soldats=%2d/%d | defenseurs=%2d/%s | +proche->FOB=%.0fm" % (t, len(alive), nTot, gda, gd0, pen), flush=True)
        if pen < 25: print("  >>> FOB PRIS par la %s !" % grades, flush=True); break
    surv = len([x for x in (rd(read_fr, "HARMATTAN_FC") or []) if len(x) > 2 and x[2] > 0.5])
    print("=== FIN %s : penetration %.0f->%.0fm | soldats %d/%d | defenseurs %s->%d ===" % (grades, pen0 or 0, pen, surv, nTot, gd0, gda), flush=True)
    b.send("{ private _v=missionNamespace getVariable [_x,[]]; { deleteVehicle _x } forEach _v; } forEach [\"HMT_FR\"];")


if __name__ == "__main__":
    main()
