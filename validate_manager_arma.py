"""validate_manager_arma — VALIDATION ARMA du MANAGER APPRIS [pile 1/5]. Le manager (entraîné en sim op_gpu)
pilote de VRAIES opérations Arma : toutes les K op-étapes il lit l'état réel, construit ses 22-obs, choisit
objectif+posture par escouade ; le cerveau gelé koth_finetuned fait la micro (postures = biais de logits).
Pont d'OBS = le point critique : reconstruire les 22-dim du sim depuis l'état Arma (positions, effectifs,
PV garnison/patrouilles/QRF séparés via les tranches de HMT_EN). Modes : --smoke (1 serveur, imprime les obs)
ou --servers N --reps M (validation de masse). Baseline : partition scriptée P-v3b = 72 % militaire."""
import time, argparse, threading, json
import numpy as np
import torch
from op_arma import OpArma, STANCES
from op_gpu import GOALS, POINTS
from train_koth_gpu import Net
from train_manager import Manager

SB = "/mnt/data/harmattan-sandbox"
DEV = "cuda:0"
COMPLEXE = np.array(POINTS["COMPLEXE"], dtype=float)
LZ = np.array(POINTS["LZ"], dtype=float)
GOAL_XY = np.array([POINTS[g] for g in GOALS], dtype=float)   # (8,2)
# géographie palier 2 (mêmes points que run_op)
SQUADS = (("SQ_APPUI", 7), ("SQ_A_OUEST", 7), ("SQ_A_EST", 7), ("SQ_RESERVE", 7))
SPAWNS = {"SQ_APPUI": POINTS["SPAWN_APPUI"], "SQ_A_OUEST": POINTS["SPAWN_AO"],
          "SQ_A_EST": POINTS["SPAWN_AE"], "SQ_RESERVE": POINTS["SPAWN_RES"]}
GARRISON = [(int(COMPLEXE[0]), int(COMPLEXE[1]), 12, 80), (15150, 16120, 4, 120), (14860, 16110, 4, 120)]
QRF_PT = POINTS["QRF_PT"]
GARR_N, PAT_N, QRF_N = 12, 8, 8          # tailles (patrouilles = 2×4)


def squad_centroid(env, si):
    al = env.alive(si)
    if not al.any(): return env.goals[si]
    return np.array([env.px[si][al].mean(), env.py[si][al].mean()])


def manager_obs(env, t, max_steps, consol_t, qrf_live):
    """Reconstruit les 22-obs du sim (op_gpu.obs) depuis l'état Arma. ORDRE IDENTIQUE au sim."""
    per_sq = []
    for si in range(env.S):
        c = squad_centroid(env, si)
        rel = (c - COMPLEXE) / 500.0
        strn = env.alive(si).sum() / 7.0
        dlz = np.linalg.norm(c - LZ) / 500.0
        per_sq += [rel[0], rel[1], strn, dlz]
    # PV ennemis par tranche de HMT_EN : garnison[0:12], patrouilles[12:20], QRF[20:]
    eal = env.en_alive()
    garr = eal[0:GARR_N].sum() / GARR_N
    patrol = eal[GARR_N:GARR_N + PAT_N].sum() / PAT_N
    qrf = (eal[GARR_N + PAT_N:].sum() / QRF_N) if env.en_n > GARR_N + PAT_N else 0.0
    en = [garr, patrol, qrf, float(qrf_live), consol_t / 20.0, t / max_steps]
    return np.array(per_sq + en, dtype=np.float32)


def run_manager_op(env, manager, brain, K=3, max_steps=80, qrf_kind="inf", verbose=False, log=None):
    """Une opération pilotée par le manager. Retourne le dict de métriques."""
    env.spawn(SPAWNS, GARRISON)
    consol_t = 0; qrf_live = False; qrf_done = False
    cur_acts = None
    for st in range(max_steps):
        # --- décision opérationnelle du manager toutes les K étapes ---
        if st % K == 0:
            o = manager_obs(env, st, max_steps, consol_t, qrf_live)
            with torch.no_grad():
                gl, sl, _ = manager(torch.as_tensor(o, device=DEV)[None])
            gidx = gl[0].argmax(-1).cpu().numpy(); sidx = sl[0].argmax(-1).cpu().numpy()
            for si in range(env.S):
                env.goals[si] = GOAL_XY[gidx[si]].copy()
                want = ["move", "assault", "suppress", "hold"][sidx[si]]
                # APPROCHE : tant qu'on est loin de l'objectif (>120 m), on MARCHE (move-transit de groupe)
                # quelle que soit la posture voulue — le cerveau gelé (entraîné au contact ~140 m) se fige
                # sinon à distance. On n'adopte la posture du manager qu'à l'arrivée. Ne touche pas op_arma.
                env.stances[si] = "move" if (want != "move" and env._goal_dist(si) > 120.0) else want
            if verbose:
                ealv=env.en_alive(); g_a=int(ealv[0:GARR_N].sum()); pertes_now=1-sum(int(env.alive(si).sum()) for si in range(env.S))/(env.S*7)
                dmin=min(np.linalg.norm(squad_centroid(env,si)-COMPLEXE) for si in range(env.S))
                print("  [op%2d] sane=%s | goals %s st %s | garr_vivants %d/12 pertes %.0f%% d_min_cx %.0f" % (
                    st, bool(np.isfinite(o).all()),
                    [GOALS[int(x)][:4] for x in gidx], [["mv","as","su","ho"][int(x)] for x in sidx],
                    g_a, 100*pertes_now, dmin), flush=True)
        # --- micro : cerveau gelé par escouade (obs 10 + biais posture) ---
        acts = []
        for si in range(env.S):
            ob = env.obs(si)
            with torch.no_grad():
                lg = brain.a_logits(torch.as_tensor(ob, dtype=torch.float32, device=DEV))
            lg = lg + torch.as_tensor(STANCES[env.stances[si]], device=DEV)
            acts.append(torch.distributions.Categorical(logits=lg).sample().cpu().numpy())
        env.step(acts)
        # --- événements : prise du complexe -> spawn QRF ; suivi consolidation ---
        eal = env.en_alive(); garr_alive = eal[0:GARR_N].sum()
        if garr_alive == 0 and not qrf_done:
            (env.spawn_qrf(QRF_PT[0], QRF_PT[1], QRF_N, tuple(COMPLEXE)) if qrf_kind == "inf"
             else env.spawn_qrf_mech(QRF_PT[0], QRF_PT[1], 6, tuple(COMPLEXE)))
            qrf_live = True; qrf_done = True
            if verbose: print("  >> QRF déclenchée (complexe pris)", flush=True)
        # consolidation : garnison morte + ≥2 escouades à <60m du complexe
        if garr_alive == 0:
            near = sum(1 for si in range(env.S) if env.alive(si).any()
                       and np.linalg.norm(squad_centroid(env, si) - COMPLEXE) < 60)
            if near >= 2: consol_t += 1
    # --- métriques finales (mêmes définitions que le sim/Arma P-v3b) ---
    eal = env.en_alive()
    garr_a = eal[0:GARR_N].sum(); pat_a = eal[GARR_N:GARR_N + PAT_N].sum(); qrf_a = eal[GARR_N + PAT_N:].sum()
    alive_tot = sum(int(env.alive(si).sum()) for si in range(env.S))
    pertes = 1 - alive_tot / (env.S * 7)
    eff_total = GARR_N + PAT_N + (QRF_N if qrf_live else 0)
    reste = garr_a + pat_a + qrf_a
    ennemi_brise = (garr_a == 0) and ((1 - reste / max(eff_total, 1)) >= 0.7)
    mil = bool(ennemi_brise and pertes <= 0.5)
    return {"mil": mil, "pertes": float(pertes), "garr_pris": bool(garr_a == 0),
            "qrf_spawn": bool(qrf_live), "qrf_reste": int(qrf_a), "consol": int(consol_t)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--servers", type=int, default=16); p.add_argument("--reps", type=int, default=32)
    p.add_argument("--K", type=int, default=3); p.add_argument("--max_steps", type=int, default=90)
    p.add_argument("--qrf", type=str, default="inf"); p.add_argument("--out", type=str, default="validate_manager.jsonl")
    a = p.parse_args()
    manager = Manager(22).to(DEV); manager.load_state_dict(torch.load("manager.pt", map_location=DEV)); manager.eval()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()

    if a.smoke:
        print("=== SMOKE Phase A : 1 opération pilotée-manager (obs imprimées) ===", flush=True)
        env = OpArma(squads=SQUADS, mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
                     log=SB + "/logs/server0.out", move=36, seed=1)
        m = run_manager_op(env, manager, brain, K=a.K, max_steps=a.max_steps, qrf_kind=a.qrf, verbose=True)
        print("[SMOKE] %s" % m, flush=True)
    else:
        # --- VALIDATION DE MASSE : 32 ops sur N serveurs (threads, 1 op/serveur à la fois) ---
        jobs = list(range(a.reps)); lock = threading.Lock(); results = []; cur = [0]
        def worker(srv):
            mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
            log = SB + "/logs/server%d.out" % srv
            while True:
                with lock:
                    if cur[0] >= len(jobs): return
                    seed = jobs[cur[0]]; cur[0] += 1
                t0 = time.time()
                try:
                    env = OpArma(squads=SQUADS, mission=mis, log=log, move=36, seed=seed)
                    m = run_manager_op(env, manager, brain, K=a.K, max_steps=a.max_steps, qrf_kind=a.qrf)
                    m["seed"] = seed; m["srv"] = srv; m["dt"] = round(time.time() - t0, 1)
                except Exception as e:
                    m = {"seed": seed, "srv": srv, "err": type(e).__name__}
                with lock:
                    results.append(m)
                    with open(a.out, "a") as f: f.write(json.dumps(m) + "\n")
                    ok = [r for r in results if "mil" in r]
                    nmil = sum(r["mil"] for r in ok)
                    print("[%d/%d] srv%d -> mil=%s garr_pris=%s qrf=%s consol=%d | cumul mil %d/%d"
                          % (len(results), len(jobs), srv, m.get("mil"), m.get("garr_pris"),
                             m.get("qrf_spawn"), m.get("consol", 0), nmil, len(ok)), flush=True)
        print("=== VALIDATION MASSE : %d ops / %d serveurs (QRF %s) | baseline scriptée 72%% ===" % (a.reps, a.servers, a.qrf), flush=True)
        th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
        for t in th: t.start()
        for t in th: t.join()
        ok = [r for r in results if "mil" in r]
        if ok:
            mil = sum(r["mil"] for r in ok) / len(ok)
            pertes = sum(r["pertes"] for r in ok) / len(ok)
            gp = sum(r["garr_pris"] for r in ok) / len(ok)
            qs = sum(r["qrf_spawn"] for r in ok) / len(ok)
            print("\n=== VERDICT MANAGER ARMA (n=%d) ===" % len(ok), flush=True)
            print("militaire %.1f%% | pertes moy %.0f%% | complexe pris %.0f%% | QRF affrontée %.0f%%"
                  % (100*mil, 100*pertes, 100*gp, 100*qs), flush=True)
            print("[seuils : >=72%% transfert réussi | 50-72%% partiel | <40%% sim sur-appris] vs scripté 72%%", flush=True)
