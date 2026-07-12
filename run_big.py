"""run_big — STRESS : 150 agents (4 escouades grossies) menent une operation sur Paros, pilotes par le cerveau
RL gele + l'officier-LLM, alimentant le dashboard tactique (staff/state.json). On MESURE : spawn OK ?, cadence
par pas, pont sous charge ?, neutralisation/pertes a la fin. C'est un test d'echelle, pas une demo propre."""
import time, json, argparse, math
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
import paros as M
import officer_op
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"; STAFF = "/home/younes/arma3-marl/staff/state.json"
HB = "/home/younes/arma3-marl/staff/big_heartbeat.json"
COL = {"SQ_APPUI": "#3b82f6", "SQ_A_OUEST": "#22c55e", "SQ_A_EST": "#f59e0b", "SQ_RESERVE": "#eab308"}
SQUADS_BIG = (("SQ_APPUI", 38), ("SQ_A_OUEST", 38), ("SQ_A_EST", 37), ("SQ_RESERVE", 37))   # = 150 agents
LLM = {}
REPORT = ("Objectif TENU PAR UNE FORCE LOURDE : ~150 hommes retranches dans Paros (noyau urbain dense + ceinture "
          "defensive sur 360 deg). Tu disposes toi aussi d'une force LOURDE (150 hommes, 4 escouades). Bataille de "
          "HAUTE INTENSITE. Terrain : crete d'appui au nord-ouest qui domine la ville, flancs ouest et est "
          "praticables, approche qui monte depuis le sud.")
_t0 = [None]


def garrison_lourde(total=150, core=18, rings=12, rad0=90, drad=70):
    """Defense lourde : noyau ville + ceinture de positions sur 360 deg autour de l'objectif."""
    cx, cy = M.COMPLEXE
    g = [(cx, cy, core, 50)]
    per = (total - core) // rings
    for i in range(rings):
        ang = 2 * math.pi * i / rings
        r = rad0 + (i % 3) * (drad // 2)                 # ceinture 90..160 m, reste a terre dans Paros
        g.append((int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang)), per, 60))
    return g


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
    # battement de coeur : cadence reelle par pas
    now = time.time()
    dt = None if _t0[0] is None else round(now - _t0[0], 2)
    _t0[0] = now
    alive = sum(int(env.dmg[si][u] < env.dmg_dead * 100) for si in range(env.S) for u in range(env.sizes[si]))
    try:
        json.dump({"step": runner.step_i, "dt_par_pas_s": dt, "agents_vivants": alive, "agents_total": sum(env.sizes),
                   "ennemis_vivants": int(env.en_alive().sum()), "pertes_pct": round(100 * runner.losses(), 1)}, open(HB, "w"))
    except Exception:
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--srv", type=int, default=2); p.add_argument("--seed", type=int, default=5)
    p.add_argument("--max_steps", type=int, default=260); p.add_argument("--acc", type=float, default=1.0)
    p.add_argument("--enemy", type=int, default=150)
    a = p.parse_args()
    N = sum(s[1] for s in SQUADS_BIG)
    GARR = garrison_lourde(total=a.enemy)
    print("=== HAUTE INTENSITE : %d vs %d (server%d, acc=%.1f) ===" % (N, sum(g[2] for g in GARR), a.srv, a.acc), flush=True)
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    print("[officier-LLM] lit la situation...", flush=True)
    try:
        d = officer_op.decide(REPORT)
    except Exception as e:
        d = {"manoeuvre": "M1", "posture": "appui-assaut", "justification": "(repli: %s)" % str(e)[:50]}
    raw = str(d.get("manoeuvre", "M1")).upper(); man = next((mk for mk in M.MANEUVERS if mk in raw), "M1")
    LLM.update({"posture": d.get("posture"), "maneuver": man, "justification": d.get("justification"), "allocation": d.get("allocation")})
    print("[LLM] manoeuvre=%s | %s" % (man, d.get("justification")), flush=True)
    env = OpArma(squads=SQUADS_BIG, mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % a.srv,
                 log=SB + "/logs/server%d.out" % a.srv, move=36, acc=a.acc, seed=a.seed)
    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = GARR[0][2]
    print("[spawn] %d amis + %d ennemis (300 IA)... (peut prendre du temps)" % (N, sum(g[2] for g in GARR)), flush=True)
    t_spawn = time.time()
    env.spawn(M.SPAWNS, GARR)
    print("[spawn] fait en %.1fs | ennemis=%d" % (time.time() - t_spawn, env.en_n), flush=True)
    runner = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=True)
    runner.opname = "HAUTE INTENSITE %dv%d / %s" % (N, env.en_n, man)
    dump(runner)
    ok = runner.run(max_steps=a.max_steps, max_wall=1500, stall_wall=400, trace=dump)
    dump(runner)
    eal = env.en_alive()
    print("\n>>> %d agents | %s | objectif %s | ennemi neutralise %.0f%% | pertes %.0f%%"
          % (N, man, "PRIS" if ok else "non pris", 100 * (1 - eal.mean()), 100 * runner.losses()), flush=True)
    print("BIG FINI", flush=True)
