"""run_maneuver — MESURE EN ARMA d'une manœuvre du répertoire doctrinal (maneuvers.py). Exécute la manœuvre
via OperationRunner + cerveau gelé koth_finetuned dans le VRAI Arma, calcule les métriques P-v3b
(militaire / complexe pris / pertes / QRF). Modes : --smoke (1 serveur, journal verbeux) ou
--servers N --reps M (table empirique de masse, threads). But : taux de succès RÉEL par manœuvre ->
le sélecteur choisira sur données mesurées, PAS sur le sim (court-circuite le mur sim-to-real)."""
import time, argparse, threading, json
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
from baptism import op_name
from enemy_profiles import apply_profile, metrics_dyn, PRO_SKILL_SQF, HUNT_SQF
import maneuvers as M

SB = "/mnt/data/harmattan-sandbox"
DEV = "cuda:0"
GARR_N, PAT_N, QRF_N = 12, 8, 8


def metrics(env, runner):
    """Métriques finales — définitions identiques au sim/Arma P-v3b et à validate_manager_arma."""
    eal = env.en_alive()
    garr_a = int(eal[0:GARR_N].sum()); pat_a = int(eal[GARR_N:GARR_N + PAT_N].sum()); qrf_a = int(eal[GARR_N + PAT_N:].sum())
    qrf_live = "qrf" in runner.qrf_done
    alive_tot = sum(int(env.alive(si).sum()) for si in range(env.S))
    pertes = 1 - alive_tot / sum(env.sizes)
    eff_total = GARR_N + PAT_N + (QRF_N if qrf_live else 0)
    reste = garr_a + pat_a + qrf_a
    ennemi_brise = (garr_a == 0) and ((1 - reste / max(eff_total, 1)) >= 0.7)
    mil = bool(ennemi_brise and pertes <= 0.5)
    return {"mil": mil, "pertes": float(pertes), "garr_pris": bool(garr_a == 0),
            "qrf_spawn": bool(qrf_live), "qrf_reste": qrf_a}


def run_one(brain, plan, srv, seed, max_steps, verbose, log_path, enemy="normal"):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=M.SQUADS, mission=mis, log=log, move=36, seed=seed)
    # [v4] profil de défense : effectifs échelonnés + (si pro) compétences montées + boucle de chasse
    garrison, prof = apply_profile(env, enemy, M.GARRISON)
    plan["garr_n"] = garrison[0][2]                     # le déclencheur QRF suit l'effectif réel
    env.spawn(M.SPAWNS, garrison)
    if prof["pro"]:   # skills montés toujours si pro ; boucle de CHASSE seulement si hunt (défaut True -> rétro-compat)
        env.b.send(PRO_SKILL_SQF + (HUNT_SQF if prof.get("hunt", True) else ""), wait=True)
    runner = OperationRunner(env, brain, plan, log_path=log_path, verbose=verbose)
    runner.run(max_steps=max_steps)
    return metrics_dyn(env, runner, garrison)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--maneuver", type=str, default="M1", choices=list(M.MANEUVERS.keys()))
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--servers", type=int, default=16); p.add_argument("--reps", type=int, default=24)
    p.add_argument("--base", type=int, default=0)   # offset serveur : permet 2 sondes // (base 0 sur srv 0-7, base 8 sur srv 8-15)
    p.add_argument("--max_steps", type=int, default=500); p.add_argument("--qrf", type=str, default="inf")
    p.add_argument("--out", type=str, default="run_maneuver.jsonl")
    p.add_argument("--enemy", type=str, default="normal", choices=["normal", "skilled", "skilled_hunt", "skilled_qrf", "mid_skill", "mid_bodies", "pro", "hardcore", "nightmare"])
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    plan = M.MANEUVERS[a.maneuver](qrf=a.qrf)

    if a.smoke:
        print("=== SMOKE %s : 1 opération Arma (journal verbeux) ===" % plan["name"], flush=True)
        m = run_one(brain, plan, srv=0, seed=1, max_steps=a.max_steps, verbose=True, log_path="op_journal.jsonl", enemy=a.enemy)
        m["op"] = op_name(a.maneuver, 1)
        print("[SMOKE %s] %s" % (a.maneuver, m), flush=True)
    else:
        jobs = list(range(a.reps)); lock = threading.Lock(); results = []; cur = [0]
        def worker(srv):
            while True:
                with lock:
                    if cur[0] >= len(jobs): return
                    seed = jobs[cur[0]]; cur[0] += 1
                t0 = time.time()
                try:
                    m = run_one(brain, plan, srv, seed, a.max_steps, False, "/dev/null", enemy=a.enemy)
                    m["seed"] = seed; m["srv"] = srv; m["dt"] = round(time.time() - t0, 1)
                except Exception as e:
                    m = {"seed": seed, "srv": srv, "err": type(e).__name__}
                m["op"] = op_name(a.maneuver, seed)   # baptême : chaque ligne = une op nommée, traçable
                with lock:
                    results.append(m)
                    with open(a.out, "a") as f: f.write(json.dumps({**m, "man": a.maneuver, "enemy": a.enemy}) + "\n")
                    ok = [r for r in results if "mil" in r]; nmil = sum(r["mil"] for r in ok)
                    print("[%d/%d] srv%d -> mil=%s garr_pris=%s qrf=%s | cumul mil %d/%d"
                          % (len(results), len(jobs), srv, m.get("mil"), m.get("garr_pris"),
                             m.get("qrf_spawn"), nmil, len(ok)), flush=True)
        print("=== MESURE MASSE %s : %d ops / %d serveurs (QRF %s) | baseline M1 scriptée 72%% ==="
              % (plan["name"], a.reps, a.servers, a.qrf), flush=True)
        th = [threading.Thread(target=worker, args=(s,)) for s in range(a.base, a.base + a.servers)]
        for t in th: t.start()
        for t in th: t.join()
        ok = [r for r in results if "mil" in r]
        if ok:
            mil = sum(r["mil"] for r in ok) / len(ok); pertes = sum(r["pertes"] for r in ok) / len(ok)
            gp = sum(r["garr_pris"] for r in ok) / len(ok); qs = sum(r["qrf_spawn"] for r in ok) / len(ok)
            print("\n=== TABLE %s (n=%d) ===" % (a.maneuver, len(ok)), flush=True)
            print("militaire %.1f%% | pertes moy %.0f%% | complexe pris %.0f%% | QRF affrontée %.0f%%"
                  % (100*mil, 100*pertes, 100*gp, 100*qs), flush=True)
