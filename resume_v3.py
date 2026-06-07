"""resume_v3 — REPRISE APPEND-ONLY de la table v3 après la mort du run (07/06 16h27).
Ne mesure QUE les ops manquantes : M6 seeds {1,8} + M7 seeds {0..15}. Défense NORMALE (harnais v3).
N'écrase RIEN : ouvre table_maneuvers_v3.jsonl en append, même format de ligne que run_maneuver.py.
Réutilise run_one (= cerveau koth_finetuned gelé dans le vrai Arma). 16 serveurs, threads."""
import time, json, threading, argparse
import torch
from run_maneuver import run_one, Net, DEV
from baptism import op_name
import maneuvers as M

OUT = "/home/younes/arma3-marl/table_maneuvers_v3.jsonl"

# Ops manquantes EXACTES (vérifiées sur le jsonl le 07/06) :
MISSING = [("M6", 1), ("M6", 8)] + [("M7", s) for s in range(16)]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--servers", type=int, default=16)
    p.add_argument("--max_steps", type=int, default=500)
    p.add_argument("--qrf", type=str, default="inf")
    a = p.parse_args()

    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    plans = {m: M.MANEUVERS[m](qrf=a.qrf) for m in {man for man, _ in MISSING}}

    jobs = list(MISSING); lock = threading.Lock(); results = []; cur = [0]
    print("=== REPRISE V3 (append) : %d ops manquantes / %d serveurs -> %s ==="
          % (len(jobs), a.servers, OUT), flush=True)

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs):
                    return
                man, seed = jobs[cur[0]]; cur[0] += 1
            t0 = time.time()
            try:
                m = run_one(brain, plans[man], srv, seed, a.max_steps, False, "/dev/null", enemy="normal")
                m["seed"] = seed; m["srv"] = srv; m["dt"] = round(time.time() - t0, 1)
            except Exception as e:
                m = {"seed": seed, "srv": srv, "err": type(e).__name__}
            m["op"] = op_name(man, seed)
            with lock:
                results.append(m)
                with open(OUT, "a") as f:
                    f.write(json.dumps({**m, "man": man, "enemy": "normal"}) + "\n")
                ok = [r for r in results if "mil" in r]; nmil = sum(r["mil"] for r in ok)
                print("[%d/%d] %s seed%d srv%d -> mil=%s garr_pris=%s qrf=%s | cumul mil %d/%d"
                      % (len(results), len(jobs), man, seed, srv, m.get("mil"),
                         m.get("garr_pris"), m.get("qrf_spawn"), nmil, len(ok)), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()
    ok = [r for r in results if "mil" in r]
    print("\n=== REPRISE TERMINÉE : %d/%d ops valides, %d erreurs ==="
          % (len(ok), len(jobs), len(results) - len(ok)), flush=True)
    print("Relancer la synthèse familles complète via run_table_v3.sh (bloc PYEOF) — sans le ': > OUT'.", flush=True)
