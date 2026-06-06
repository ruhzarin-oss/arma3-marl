"""wargame_op — WARGAMING STATISTIQUE de l'opération HARMATTAN-1 : la même opération répétée en masse
sur M serveurs headless EN PARALLÈLE (1 opération par serveur, threads), pour comparer des VARIANTES DE PLAN
en taux de succès / pertes / phase d'échec — la méthode des 7 lois appliquée à un plan d'état-major.
Usage : wargame_op.py --servers 10 --reps 30 (reps répartis sur les serveurs, plans A/B alternés)"""
import argparse, json, threading, time
import torch
from op_arma import OpArma, OperationRunner, DEV, SB
from train_koth_gpu import Net
import run_op as OP                                     # géographie + make_plan (source unique de vérité)

p = argparse.ArgumentParser()
p.add_argument("--servers", type=int, default=10)
p.add_argument("--reps", type=int, default=30, help="nombre total d'opérations (réparties A/B alternés)")
p.add_argument("--out", type=str, default="wargame_results.jsonl")
p.add_argument("--qrf", type=str, default="inf", choices=["inf", "mech"])
p.add_argument("--palier", type=int, default=1, choices=[1, 2])
a = p.parse_args()

net = Net(10, 4, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/koth_finetuned.pt", map_location=DEV)); net.eval()

jobs = [("A" if i % 2 == 0 else "B", i) for i in range(a.reps)]      # plans alternés, seed = i
lock = threading.Lock(); results = []; jcursor = [0]

def worker(srv):
    mission = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    while True:
        with lock:
            if jcursor[0] >= len(jobs): return
            plan, seed = jobs[jcursor[0]]; jcursor[0] += 1
        t0 = time.time()
        try:
            if a.palier == 2:
                env = OpArma(squads=OP.SQUADS_P2, mission=mission, log=log, seed=seed)
                env.spawn(OP.SPAWNS_P2, garrison=OP.GARRISON_P2)
                mplan = OP.make_plan_p2(plan, qrf=a.qrf)
            else:
                env = OpArma(squads=(("SQ_APPUI", 7), ("SQ_ASSAUT", 7)), mission=mission, log=log, seed=seed)
                env.spawn({"SQ_APPUI": OP.SPAWN_APPUI, "SQ_ASSAUT": OP.SPAWN_ASSAUT},
                          garrison=[(OP.COMPLEXE[0], OP.COMPLEXE[1], 8, 80)])
                mplan = OP.make_plan(plan, qrf=a.qrf)
            runner = OperationRunner(env, net, mplan,
                                     log_path="logs_train/wg_srv%d.jsonl" % srv, verbose=False)
            ok = runner.run(max_steps=500)
            veh = ("détruit" if env.vehdmg >= 70 else ("intact" if env.has_veh else "n/a"))
            rec = {"plan": plan, "seed": seed, "srv": srv, "succes": bool(ok), "vehicule": veh,
                   "pertes": round(runner.losses(), 3), "ennemis_restants": int(env.en_alive().sum()),
                   "steps": runner.step_i, "duree_s": round(time.time() - t0, 1)}
        except Exception as e:
            rec = {"plan": plan, "seed": seed, "srv": srv, "succes": None, "erreur": type(e).__name__}
        with lock:
            results.append(rec)
            with open(a.out, "a") as f: f.write(json.dumps(rec) + "\n")
            done = len(results); okA = sum(1 for r in results if r["plan"] == "A" and r.get("succes"))
            nA = sum(1 for r in results if r["plan"] == "A" and r.get("succes") is not None)
            okB = sum(1 for r in results if r["plan"] == "B" and r.get("succes"))
            nB = sum(1 for r in results if r["plan"] == "B" and r.get("succes") is not None)
            print("[%d/%d] srv%d plan %s -> %s | pertes %.0f%% | cumul : A %d/%d, B %d/%d"
                  % (done, len(jobs), srv, plan, rec.get("succes"), 100 * rec.get("pertes", 0), okA, nA, okB, nB), flush=True)

threads = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
t0 = time.time()
for t in threads: t.start()
for t in threads: t.join()

ok = [r for r in results if r.get("succes") is not None]
print("\n=== WARGAME TERMINÉ (%.0f min) — %d opérations valides ===" % ((time.time() - t0) / 60, len(ok)), flush=True)
for plan in ("A", "B"):
    rs = [r for r in ok if r["plan"] == plan]
    if not rs: continue
    sr = sum(r["succes"] for r in rs) / len(rs)
    pl = sum(r["pertes"] for r in rs) / len(rs)
    en = sum(r["ennemis_restants"] for r in rs) / len(rs)
    print("PLAN %s (%s) : succès %.2f | pertes moy %.0f%% | ennemis restants moy %.1f | n=%d"
          % (plan, "appui d'abord" if plan == "A" else "assaut direct", sr, 100 * pl, en, len(rs)), flush=True)
