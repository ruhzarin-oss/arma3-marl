#!/usr/bin/env python3
"""full_stack.py — G.1 : LES 3 ETAGES EN UNE BOUCLE.
  GENERAL (Qwen)      : lit l'assaut -> intention (PRESSER / FLANC_G / FLANC_D).
  SOUS-OFFICIER (commander.pt) : place les 2 elements vers l'objectif (avance coordonnee, LAMBS execute).
  ORCHESTRATION (orchestration_arma) : tactique de chaque soldat (fumi/grenade/...) qui se COMPOSE par-dessus.
Assaut loyal (8 vs 8), score = penetration + survie. Le general biaise l'axe ; le commandant avance ; les agents composent."""
import sys, time, ast, math, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch, torch.nn as nn

CKC = "/home/younes/compose-embodiment/commander.pt"
CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
CX, CY = 4279, 3560
S = 200.0; R_PLACE = 95.0; NG = 8; MAXT = 14
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def general_intent(dist, nguards, nalive):
    """ETAGE 1 (Qwen) : l'intention d'assaut."""
    import requests, json
    prompt = ("Tu commandes un assaut : %d hommes en 2 elements, a ~%dm d'un objectif defendu par %d gardes retranches. "
              "But : PRENDRE l'objectif avec le moins de pertes. Choisis l'intention. "
              "Reponds STRICT JSON {\"intent\":\"PRESSER|FLANC_G|FLANC_D\",\"raison\":\"court\"}.") % (nalive, dist, nguards)
    try:
        r = requests.post("http://localhost:11434/v1/chat/completions", json={
            "model": "qwen2.5:14b", "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "response_format": {"type": "json_object"}}, timeout=60)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return {"intent": "PRESSER", "raison": "defaut(%s)" % str(e)[:40]}


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
    ap = argparse.ArgumentParser(); ap.add_argument("--steps", type=int, default=12); a = ap.parse_args()
    b = NativeBridge(port=5816)
    for f in ("orch_features_v6.sqf", "tactics_exec_v2.sqf"):
        b.send('call compile preprocessFileLineNumbers "%s";' % f)
    cnet = CNet(17, 4); cnet.load_state_dict(torch.load(CKC, map_location="cpu")); cnet.eval()
    onet = OrchNet(); onet.load_state_dict(torch.load(CKO, map_location="cpu")); onet.eval()
    print("[full-stack] general Qwen + commander.pt + orchestration charges. Objectif [%d,%d]" % (CX, CY), flush=True)

    setup = ('[] spawn { HMT_CX=%d; HMT_CY=%d; '
             'if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR }; if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS }; '
             'private _ge=createGroup east; HMT_GUARDS=[]; '
             'for "_i" from 0 to 7 do { private _ang=_i*45; private _g=_ge createUnit ["O_Soldier_F",[HMT_CX+24*sin _ang,HMT_CY+24*cos _ang,0],[],0,"NONE"]; _g setPosATL [HMT_CX+24*sin _ang,HMT_CY+24*cos _ang,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; _g setSkill 0.5; HMT_GUARDS pushBack _g; }; '
             'HMT_GA=createGroup west; HMT_GB=createGroup west; HMT_FR=[]; '
             'for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%%2)*8-4); private _sy=HMT_CY-130-_i*5; private _grp=if (_i<4) then {HMT_GA} else {HMT_GB}; '
             'private _s=_grp createUnit ["B_recon_F",[_sx,_sy,0],[],0,"NONE"]; _s setPosATL [_sx,_sy,0]; _s setSkill 0.6; _s setBehaviour "AWARE"; _s setCombatMode "RED"; _s addMagazine "SmokeShell"; HMT_FR pushBack _s; }; '
             'sleep 3; { private _r=_x; { _x reveal [_r,3] } forEach (allUnits select {side _x==east && alive _x && _x distance _r<500}); } forEach HMT_FR; '
             '(format ["HARMATTAN_ASETUP fr=%%1", count HMT_FR]) call HMT_EMIT; };') % (CX, CY)
    b.query(setup, r"HARMATTAN_ASETUP fr=(\d+)", want=1, timeout=15)
    time.sleep(16)

    read_fr = ('private _o=[]; { private _p=getPosATL _x; _o pushBack [round((_p select 0)-%d), round((_p select 1)-%d), (if (alive _x) then {1} else {0})]; } forEach HMT_FR; (format ["HARMATTAN_FC %%1", _o]) call HMT_EMIT;') % (CX, CY)
    read_gd = ('private _o=[]; { if (alive _x) then { private _q=getPosATL _x; _o pushBack [round((_q select 0)-%d), round((_q select 1)-%d)]; } } forEach HMT_GUARDS; (format ["HARMATTAN_GD %%1", _o]) call HMT_EMIT;') % (CX, CY)

    def rd(sqf, tag):
        r = b.query(sqf, tag + r" (\[.*\])", want=1, timeout=10)
        try: return ast.literal_eval(r[-1].group(1)) if r else None
        except Exception: return None

    print("=== FULL-STACK : Commandant (avance) -> Orchestration (compose) ; General reflechit pendant que l'escouade bouge ===", flush=True)
    pen_start = None
    bias = 0                                                          # le commandant demarre TOUT DE SUITE (pas d'attente Qwen)
    for t in range(a.steps):
        agents = rd(read_fr, "HARMATTAN_FC")
        if not agents or len(agents) < 8:
            time.sleep(1); continue
        guards = rd(read_gd, "HARMATTAN_GD") or []
        # --- ETAGE 2 : le commandant place les 2 elements (avec le biais d'axe du general) ---
        obs = build_obs(agents, guards, t)
        with torch.no_grad():
            mu, _ = cnet(obs); act = mu.clamp(-1, 1).view(2, 2)
        t0 = [CX + float(act[0, 0]) * R_PLACE + bias, CY + float(act[0, 1]) * R_PLACE]
        t1 = [CX + float(act[1, 0]) * R_PLACE + bias, CY + float(act[1, 1]) * R_PLACE]
        order = ('HMT_T0=[%.1f,%.1f,0]; HMT_T1=[%.1f,%.1f,0]; { _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach HMT_FR; '
                 '{ deleteWaypoint _x } forEach (waypoints HMT_GA + waypoints HMT_GB); '
                 'private _wa=HMT_GA addWaypoint [HMT_T0,0]; _wa setWaypointType "MOVE"; _wa setWaypointBehaviour "COMBAT"; _wa setWaypointCombatMode "RED"; HMT_GA setCurrentWaypoint _wa; '
                 'private _wb=HMT_GB addWaypoint [HMT_T1,0]; _wb setWaypointType "MOVE"; _wb setWaypointBehaviour "COMBAT"; _wb setWaypointCombatMode "RED"; HMT_GB setCurrentWaypoint _wb;') % (t0[0], t0[1], t1[0], t1[1])
        b.send(order)
        # --- ETAGE 3 : l'orchestration ajoute la tactique de chaque soldat (compose par-dessus) ---
        import re
        rs = b.query("[[%d,%d,0],8,west] call HMT_ORCH_SNAP;" % (CX, CY), r'HARMATTAN_ORCH (\[.*\]) \| (\[.*\])', want=1, timeout=8)
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
        if t == 0:                                                   # ETAGE 1 : le general reflechit PENDANT que l'escouade avance (waypoint deja pose)
            al0 = [x for x in agents if x[2] > 0.5]
            d0 = min((math.hypot(x[0], x[1]) for x in al0), default=130)
            intent = general_intent(int(d0), 8, len(al0))
            bias = {"PRESSER": 0, "FLANC_G": -45, "FLANC_D": 45}.get(intent.get("intent", "PRESSER"), 0)
            print("[GENERAL Qwen] intention=%s (%s) -> biais axe=%+dm (des t=1)" % (intent.get("intent"), intent.get("raison", "")[:50], bias), flush=True)
        time.sleep(6.0)
        alive = [ag for ag in agents if ag[2] > 0.5]
        pen = min((math.hypot(ag[0], ag[1]) for ag in alive), default=999)
        if pen_start is None: pen_start = pen
        print("  t=%2d | commandant A(%+.0f,%+.0f) B(%+.0f,%+.0f) | orch %s | vivants=%d | ->objectif=%.0fm"
              % (t, t0[0]-CX, t0[1]-CY, t1[0]-CX, t1[1]-CY, odist, len(alive), pen), flush=True)
        if pen < 30: print("  >>> OBJECTIF PRIS par le full-stack !", flush=True); break
    surv = len([x for x in (rd(read_fr, "HARMATTAN_FC") or []) if len(x) > 2 and x[2] > 0.5])
    print("=== FIN full-stack : penetration %.0f -> %.0fm | survivants=%d/8 ===" % (pen_start or 0, pen, surv), flush=True)
    b.send("{ private _v=missionNamespace getVariable [_x,[]]; { deleteVehicle _x } forEach _v; } forEach [\"HMT_FR\",\"HMT_GUARDS\"];")


if __name__ == "__main__":
    main()
