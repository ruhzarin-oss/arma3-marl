#!/usr/bin/env python3
"""command_stack.py — LE SYSTEME INTEGRE (assemblage final). Toute la chaine en UNE boucle :
  GENERAL (Qwen)          -> intention d'assaut (non-bloquant).
  OFFICIERS (recursif army)-> Capitaine -> Lieutenants -> Sergents (commander.pt) placent la force.
  SERGENTS -> soldats (LAMBS execute le feu-et-mouvement).
  ORCHESTRATION -> tactique de chaque soldat (fumi/grenade/...) qui se COMPOSE par-dessus.
Un seul lancement -> l'assaut complet, tous les etages. --branch regle l'echelon (3=Lt, 3,3=Cap, 3,3,3=Col)."""
import sys, time, ast, math, argparse, re
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import FOBS
import torch, torch.nn as nn

CKC = "/home/younes/compose-embodiment/commander.pt"
CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
S = 200.0; R_PLACE = 95.0; NG = 8
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1); self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__(); s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()); s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def fan(obj, n, w):
    return [list(obj)] if n <= 1 else [[obj[0] + w * (i / (n - 1) - 0.5), obj[1]] for i in range(n)]


def allocate(obj, branch, widths, d=0):
    if d >= len(branch):
        return [list(obj)]
    out = []
    for s in fan(obj, branch[d], widths[d]):
        out += allocate(s, branch, widths, d + 1)
    return out


def sergent_obs(sol, guards, sub, t, maxt=14):
    ax, ay = sub; ag = [[s[0] - ax, s[1] - ay, s[2]] for s in sol]; gd = [[g[0] - ax, g[1] - ay] for g in guards]
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


def general_intent(dist, nguards, nalive):
    import requests, json
    p = ("Tu commandes un assaut : %d hommes, ~%dm d'un objectif tenu par %d defenseurs. But: PRENDRE avec peu de pertes. "
         "Reponds STRICT JSON {\"intent\":\"PRESSER|FLANC_G|FLANC_D\",\"raison\":\"court\"}.") % (nalive, dist, nguards)
    try:
        r = requests.post("http://localhost:11434/v1/chat/completions", json={"model": "qwen2.5:14b",
            "messages": [{"role": "user", "content": p}], "temperature": 0.2, "response_format": {"type": "json_object"}}, timeout=60)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return {"intent": "PRESSER", "raison": str(e)[:30]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fob", default="M1"); ap.add_argument("--steps", type=int, default=18); ap.add_argument("--branch", default="3,3")
    a = ap.parse_args()
    branch = [int(x) for x in a.branch.split(",")]; widths = [150, 55, 25][:len(branch)]
    nS = 1
    for x in branch: nS *= x
    nTot = nS * 8
    b = NativeBridge(port=5816)
    cnet = CNet(17, 4); cnet.load_state_dict(torch.load(CKC, map_location="cpu")); cnet.eval()
    onet = OrchNet(); onet.load_state_dict(torch.load(CKO, map_location="cpu")); onet.eval()
    fob = next(([f[1], f[2]] for f in FOBS if f[0] == a.fob), [4279, 3856]); CX, CY = fob
    grade = {2: "LIEUTENANT", 3: "CAPITAINE", 4: "COLONEL"}.get(len(branch) + 1, "OFFICIER")
    print("[SYSTEME INTEGRE] General + %s(%d) + orchestration vs FOB %s. branch=%s" % (grade, nTot, a.fob, branch), flush=True)

    setup = ('[] spawn { HMT_CX=%d; HMT_CY=%d; if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR }; HMT_FR=[]; HMT_SG=[]; private _ns=%d; '
             'for "_sg" from 0 to (_ns-1) do { private _ga=createGroup west; private _gb=createGroup west; HMT_SG pushBack [_ga,_gb]; private _lat=((_sg/((_ns-1) max 1))-0.5)*260; '
             '  for "_i" from 0 to 7 do { private _grp=if (_i<4) then {_ga} else {_gb}; private _s=_grp createUnit ["B_recon_F",[HMT_CX+_lat+((_i%%2)*8-4),HMT_CY-170-(_i*5),0],[],0,"NONE"]; '
             '  _s setPosATL [HMT_CX+_lat+((_i%%2)*8-4),HMT_CY-170-(_i*5),0]; _s setSkill 0.6; _s setBehaviour "AWARE"; _s setCombatMode "RED"; _s addMagazine "SmokeShell"; HMT_FR pushBack _s; }; }; '
             'sleep 3; { private _r=_x; { _x reveal [_r,3] } forEach (allUnits select {side _x==east && alive _x && _x distance _r<700}); } forEach HMT_FR; '
             '(format ["HARMATTAN_ASETUP fr=%%1", count HMT_FR]) call HMT_EMIT; };') % (CX, CY, nS)
    sr = b.query(setup, r"HARMATTAN_ASETUP fr=(\d+)", want=1, timeout=25)
    print("[DEBUG setup] fr spawnes =", sr[-1].group(1) if sr else "AUCUN RETOUR", flush=True)
    for f in ("orch_features_v6.sqf", "tactics_exec_v2.sqf"):     # chargements APRES le setup (pont natif reste synchro)
        b.send('call compile preprocessFileLineNumbers "%s";' % f)
    time.sleep(17)

    read_fr = ('private _o=[]; { private _p=getPosATL _x; _o pushBack [round((_p select 0)-%d), round((_p select 1)-%d), (if (alive _x) then {1} else {0})]; } forEach HMT_FR; (format ["HARMATTAN_FC %%1", _o]) call HMT_EMIT;') % (CX, CY)
    read_gd = ('private _o=[]; { if (alive _x && (_x distance [%d,%d,0])<230) then { private _q=getPosATL _x; _o pushBack [round((_q select 0)-%d), round((_q select 1)-%d)]; } } forEach (allUnits select {side _x==east}); (format ["HARMATTAN_GD %%1", _o]) call HMT_EMIT;') % (CX, CY, CX, CY)

    def rd(sqf, tag):
        r = b.query(sqf, tag + r" (\[.*\])", want=1, timeout=12)
        try: return ast.literal_eval(r[-1].group(1)) if r else None
        except Exception: return None

    print("=== SYSTEME INTEGRE : General -> %s (recursion) -> Sergents -> Orchestration ===" % grade, flush=True)
    pen0 = gd0 = None; bias = 0; pen = 999.0; alive = []; gda = 0
    for t in range(a.steps):
        agents = rd(read_fr, "HARMATTAN_FC")
        if t < 3:
            print("  [DEBUG t=%d] agents lus =" % t, (len(agents) if agents else agents), flush=True)
        if not agents or len(agents) < 8:
            time.sleep(1); continue
        guards = rd(read_gd, "HARMATTAN_GD") or []
        if gd0 is None: gd0 = len(guards)
        subs = allocate([bias, 0], branch, widths)                 # le general biaise l'axe ; la recursion place les sergents
        parts = []
        for sg in range(nS):
            sol = agents[sg * 8:(sg + 1) * 8]
            if len(sol) < 8:
                continue
            sub = subs[sg]
            with torch.no_grad():
                mu, _ = cnet(sergent_obs(sol, guards, sub, t)); act = mu.clamp(-1, 1).view(2, 2)
            wx, wy = CX + sub[0], CY + sub[1]
            t0 = [wx + float(act[0, 0]) * R_PLACE, wy + float(act[0, 1]) * R_PLACE]; t1 = [wx + float(act[1, 0]) * R_PLACE, wy + float(act[1, 1]) * R_PLACE]
            parts.append(('private _ga=(HMT_SG select %d) select 0; private _gb=(HMT_SG select %d) select 1; { _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach (units _ga+units _gb); '
                          '{ deleteWaypoint _x } forEach (waypoints _ga+waypoints _gb); private _wa=_ga addWaypoint [[%.1f,%.1f,0],0]; _wa setWaypointType "MOVE"; _wa setWaypointCombatMode "RED"; _ga setCurrentWaypoint _wa; '
                          'private _wb=_gb addWaypoint [[%.1f,%.1f,0],0]; _wb setWaypointType "MOVE"; _wb setWaypointCombatMode "RED"; _gb setCurrentWaypoint _wb;') % (sg, sg, t0[0], t0[1], t1[0], t1[1]))
        for i in range(0, len(parts), 3):
            b.send(" ".join(parts[i:i + 3])); time.sleep(0.12)
        # --- ORCHESTRATION : tactique de chaque soldat, composee par-dessus l'avance ---
        rs = b.query("[[%d,%d,0],%d,west] call HMT_ORCH_SNAP;" % (CX, CY, min(nTot, 30)), r'HARMATTAN_ORCH (\[.*\]) \| (\[.*\])', want=1, timeout=8)
        odist = {}
        if rs:
            try: vs = ast.literal_eval(rs[-1].group(1))
            except Exception: vs = []
            ids = re.findall(r'(\d+:\d+(?::\d+)*)', rs[-1].group(2))
            if vs:
                with torch.no_grad(): tacs = onet(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
                if len(ids) == len(tacs):
                    b.send("[%s,%s] call HMT_TAC_DISPATCH;" % ("[" + ",".join('"%s"' % i for i in ids) + "]", tacs))
                from collections import Counter
                odist = dict(Counter(TAC[x] for x in tacs))
        if t == 0:                                                  # general reflechit PENDANT que l'assaut avance (non-bloquant)
            al = [x for x in agents if x[2] > 0.5]; d0 = min((math.hypot(x[0], x[1]) for x in al), default=160)
            intent = general_intent(int(d0), len(guards), len(al)); bias = {"PRESSER": 0, "FLANC_G": -50, "FLANC_D": 50}.get(intent.get("intent", "PRESSER"), 0)
            print("[GENERAL] %s (%s) -> biais=%+dm" % (intent.get("intent"), intent.get("raison", "")[:45], bias), flush=True)
        time.sleep(5.5)
        alive = [ag for ag in agents if ag[2] > 0.5]; pen = min((math.hypot(ag[0], ag[1]) for ag in alive), default=999)
        gda = len(rd(read_gd, "HARMATTAN_GD") or [])
        if pen0 is None: pen0 = pen
        print("  t=%2d | soldats=%2d/%d | defenseurs=%2d | orch %s | ->FOB=%.0fm" % (t, len(alive), nTot, gda, odist, pen), flush=True)
        if pen < 25:
            print("  >>> FOB PRIS — chaine complete (General->%s->orchestration) !" % grade, flush=True); break
    print("=== FIN systeme integre : penetration %.0f->%.0fm | soldats %d/%d | defenseurs %s->%d ===" % (pen0 or 0, pen, len(alive), nTot, gd0, gda), flush=True)
    b.send("{ private _v=missionNamespace getVariable [_x,[]]; { deleteVehicle _x } forEach _v; } forEach [\"HMT_FR\"];")


if __name__ == "__main__":
    main()
