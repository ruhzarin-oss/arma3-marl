"""run_duel — DUEL SYMETRIQUE : 150 BLUFOR (agents RL + officier-LLM qui choisit la manoeuvre) contre 150 OPFOR
(memes agents RL, MAIS sans LLM : defense fixe par secteurs). Les DEUX camps sont pilotes par le meme cerveau gele ;
seul BLUFOR a le commandant-LLM. Question mesuree : la couche de commandement fait-elle la difference ?

BLUFOR garde tout le pipeline teste (OperationRunner = machine de phases + contingences). OPFOR est pilote DANS le
callback de trace : a chaque pas, on lit la situation, on passe le cerveau sur chaque secteur OPFOR, on envoie les ordres.
"""
import time, json, argparse, math
import numpy as np
import torch
from op_arma import OpArma, OperationRunner, STANCES
from train_koth_gpu import Net
import paros as M
import officer_op
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"; STAFF = "/home/younes/arma3-marl/staff/state.json"
HB = "/home/younes/arma3-marl/staff/duel_heartbeat.json"
COL = {"SQ_APPUI": "#3b82f6", "SQ_A_OUEST": "#22c55e", "SQ_A_EST": "#f59e0b", "SQ_RESERVE": "#eab308"}
SQUADS_BLU = (("SQ_APPUI", 38), ("SQ_A_OUEST", 38), ("SQ_A_EST", 37), ("SQ_RESERVE", 37))   # 150 BLUFOR
LLM = {}
REPORT = ("Objectif Paros TENU PAR 150 hommes RETRANCHES (noyau urbain + ceinture defensive 360 deg, defense reactive). "
          "Tu disposes d'une force LOURDE de 150 hommes (4 escouades). Bataille de HAUTE INTENSITE, force contre force. "
          "Terrain : crete d'appui au nord-ouest qui domine la ville, flancs ouest et est praticables, approche sud.")
_t0 = [None]


def opf_secteurs(total=150):
    """Defense OPFOR : noyau ville (hold) + ceinture de secteurs (suppress) sur 360 deg. -> (x,y,n,stance)."""
    cx, cy = M.COMPLEXE
    rings = 10
    per = (total - 20) // rings
    secs = [(cx, cy, 20, "hold")]
    for i in range(rings):
        ang = 2 * math.pi * i / rings
        r = 120 + (i % 2) * 30                       # 120/150 m : reste dans Paros (a terre)
        secs.append((int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang)), per, "suppress"))
    return secs


def spawn_opfor(env, secs, skill=0.45):
    """Cree les unites OPFOR EST par secteur, poussees dans HMT_EN (PAS de taskPatrol : c'est le cerveau qui pilote)."""
    sqf = ""
    groups = []          # (i0, i1, (gx,gy), stance)
    idx = 0
    for k, (x, y, n, stance) in enumerate(secs):
        rad = max(7, int(0.5 * n))
        sqf += ('private _g%d = createGroup east;\n'
                'for "_a" from 0 to %d do {\n'
                '  _g%d createUnit ["O_Soldier_F", [%d + %d*(cos (360*_a/%d)), %d + %d*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
                '  private _u = (units _g%d) select ((count (units _g%d))-1);\n'
                '  _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u setSkill %.2f; _u allowFleeing 0; HMT_EN pushBack _u;\n};\n'
                % (k, n - 1, k, x, rad, n, y, rad, n, k, k, skill))
        groups.append((idx, idx + n, (x, y), stance)); idx += n
    sqf += 'diag_log "HARMATTAN_OPFSPAWN";\n'
    env.b.send(sqf, wait=True); time.sleep(4.0)
    env.en_n = idx
    env.epx = np.zeros(idx); env.epy = np.zeros(idx); env.edmg = np.zeros(idx)
    env.read()
    return groups


def compute_obs(px, py, al, gx, gy, epx, epy, eal, S, sight):
    """Memes 10 features que l'entrainement KOTH, pour un groupe quelconque (own vs enemy)."""
    n = len(px)
    ox = (px - gx) / S; oy = (py - gy) / S
    dgx = (gx - px) / S; dgy = (gy - py) / S
    dx = px[None, :] - px[:, None]; dy = py[None, :] - py[:, None]
    d2 = np.where(np.eye(n, dtype=bool) | (~al)[None, :], 1e18, dx * dx + dy * dy)
    jm = d2.argmin(1); adx = dx[np.arange(n), jm] / S; ady = dy[np.arange(n), jm] / S
    nm = d2.min(1) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
    if len(epx) and eal.any():
        ex = epx[None, :] - px[:, None]; ey = epy[None, :] - py[:, None]
        ed2 = np.where(eal[None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(1)
        edx = ex[np.arange(n), km]; edy = ey[np.arange(n), km]
        nd = np.sqrt(ed2.min(1)); seen = (nd <= sight) & (ed2.min(1) < 1e18)
        edx = (edx / S) * seen; edy = (edy / S) * seen
    else:
        edx = np.zeros(n); edy = np.zeros(n)
    return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, np.zeros(n)], 1).astype(np.float32)


def make_drive(env, brain, opf_groups, move=26.0):
    dead = env.dmg_dead * 100

    def drive(runner):
        # --- position de TOUT le BLUFOR (= ennemi pour OPFOR) ---
        BX = np.concatenate([env.px[si] for si in range(env.S)])
        BY = np.concatenate([env.py[si] for si in range(env.S)])
        BAL = np.concatenate([env.alive(si) for si in range(env.S)])
        cmds = []
        for (a, b, (gx, gy), stance) in opf_groups:
            ox = env.epx[a:b]; oy = env.epy[a:b]; al = env.edmg[a:b] < dead
            if not al.any():
                continue
            obs = compute_obs(ox, oy, al, gx, gy, BX, BY, BAL, env.scale, env.sight)
            with torch.no_grad():
                lg = brain.a_logits(torch.as_tensor(obs, dtype=torch.float32, device=DEV))
            lg = lg + torch.as_tensor(STANCES[stance], device=DEV)
            acts = torch.distributions.Categorical(logits=lg).sample().cpu().numpy()
            tox = gx - ox; toy = gy - oy; tn = np.sqrt(tox ** 2 + toy ** 2) + 1e-6
            for i in range(b - a):
                if not al[i]:
                    continue
                gi = a + i; m = int(acts[i])
                if m == 1:                                   # avancer vers le secteur (rare en hold)
                    tx = int(ox[i] + tox[i] / tn[i] * move); ty = int(oy[i] + toy[i] / tn[i] * move)
                    cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {_u setUnitPos "MIDDLE"; _u doMove [%d,%d,0];};' % (gi, tx, ty))
                elif m == 2:                                 # suppresser : debout, l'IA Arma tire (COMBAT)
                    cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "UP";};' % gi)
                elif m == 3:                                 # couvert
                    cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "DOWN";};' % gi)
                else:                                        # tenir
                    cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % gi)
        if cmds:
            env.b.send("\n".join(cmds), wait=True)
        dump(runner)
    return drive


def dump(runner):
    env = runner.env
    sq = {}
    for si, nm in enumerate(env.squads):
        units = [[int(env.px[si][u]), int(env.py[si][u]), int(env.dmg[si][u] < env.dmg_dead * 100)] for u in range(env.sizes[si])]
        sq[nm] = {"color": COL.get(nm, "#ddd"), "units": units, "goal": [int(env.goals[si][0]), int(env.goals[si][1])], "stance": env.stances[si]}
    en = [[int(env.epx[k]), int(env.epy[k]), int(env.edmg[k] < env.dmg_dead * 100)] for k in range(env.en_n)]
    st = {"op": runner.opname, "step": runner.step_i, "losses": round(runner.losses(), 3), "squads": sq, "enemies": en,
          "pts": {"COMPLEXE": list(M.COMPLEXE), "CRETE": list(M.CRETE), "FLANC_O": list(M.FLANC_O), "FLANC_E": list(M.FLANC_E), "QRF": list(M.QRF_PT)},
          "llm": LLM}
    try:
        json.dump(st, open(STAFF, "w"))
    except Exception:
        pass
    now = time.time(); dt = None if _t0[0] is None else round(now - _t0[0], 2); _t0[0] = now
    blu = sum(int(env.alive(si).sum()) for si in range(env.S))
    try:
        json.dump({"step": runner.step_i, "dt_par_pas_s": dt, "BLUFOR_vivants": blu,
                   "OPFOR_vivants": int(env.en_alive().sum()), "BLUFOR_total": sum(env.sizes), "OPFOR_total": env.en_n},
                  open(HB, "w"))
    except Exception:
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--srv", type=int, default=2); p.add_argument("--seed", type=int, default=5)
    p.add_argument("--max_steps", type=int, default=260); p.add_argument("--acc", type=float, default=1.0)
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    print("=== DUEL 150 BLUFOR (RL+LLM) vs 150 OPFOR (RL, sans LLM) — server%d acc=%.1f ===" % (a.srv, a.acc), flush=True)
    print("[officier-LLM BLUFOR] lit la situation...", flush=True)
    try:
        d = officer_op.decide(REPORT)
    except Exception as e:
        d = {"manoeuvre": "M1", "justification": "(repli: %s)" % str(e)[:50]}
    raw = str(d.get("manoeuvre", "M1")).upper(); man = next((mk for mk in M.MANEUVERS if mk in raw), "M1")
    LLM.update({"posture": d.get("posture"), "maneuver": man, "justification": d.get("justification")})
    print("[LLM] manoeuvre=%s | %s" % (man, d.get("justification")), flush=True)
    env = OpArma(squads=SQUADS_BLU, mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % a.srv,
                 log=SB + "/logs/server%d.out" % a.srv, move=36, acc=a.acc, seed=a.seed)
    plan = M.MANEUVERS[man](qrf="none"); plan.pop("qrf_on_garrison", None)        # pas de renfort scripte : duel pur
    secs = opf_secteurs(150)
    GARR = [(x, y, n, 22) for (x, y, n, st) in secs]                              # spawn OPFOR par le chemin garnison EPROUVE (peuple HMT_EN)
    print("[spawn] 150 BLUFOR + %d OPFOR..." % sum(s[2] for s in secs), flush=True)
    t = time.time(); env.spawn(M.SPAWNS, GARR)
    # retirer les waypoints de patrouille -> defense statique : c'est le cerveau RL qui pilote OPFOR
    env._query('{ private _g=_x; while {count waypoints _g > 0} do {deleteWaypoint [_g,0]}; } forEach (allGroups select {side _x == east}); diag_log "HARMATTAN_NOWP";', settle=1.0)
    opf_groups = []; idx = 0
    for (x, y, n, st) in secs:
        opf_groups.append((idx, idx + n, (x, y), st)); idx += n
    print("[spawn] 300 IA pretes en %.1fs (OPFOR=%d)" % (time.time() - t, env.en_n), flush=True)
    runner = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=True)
    runner.opname = "DUEL 150v150 RL / BLUFOR=%s+LLM vs OPFOR=defense" % man
    drive = make_drive(env, brain, opf_groups)
    dump(runner)
    ok = runner.run(max_steps=a.max_steps, max_wall=1600, stall_wall=450, trace=drive)
    dump(runner)
    blu = sum(int(env.alive(si).sum()) for si in range(env.S)); opf = int(env.en_alive().sum())
    print("\n>>> DUEL fini | BLUFOR %d/150 vivants (pertes %.0f%%) | OPFOR %d/150 vivants | objectif %s"
          % (blu, 100 * runner.losses(), opf, "PRIS" if ok else "non pris"), flush=True)
    print("DUEL FINI", flush=True)
