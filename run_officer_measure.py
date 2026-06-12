"""run_officer_measure — JALON 1.5 : OFFICIER ADAPTATIF vs M3-FIXE, posture aleatoire par op.
Chaque (seed, posture) joue dans les DEUX conditions (meme defense, meme seed) -> on compare le taux de
succes militaire. Parallelise sur la flotte. Question : le commandement adaptatif bat-il le commandant tetu
QUAND L'ENNEMI VARIE ? L'edge attendu vient des postures ou M3 n'est PAS champion (elastic/herisson/appat/sortie)."""
import argparse, threading, json, time
import torch
from op_arma import OperationRunner
from train_koth_gpu import Net
import maneuvers as M
import officer_live
from enemy_profiles import metrics_dyn

DEV = "cuda:0"
POSTURES = ["skilled", "skilled_react", "skilled_react_depth", "skilled_mobile",
            "skilled_elastic", "skilled_herisson", "skilled_appat", "skilled_sortie"]
SH = {"skilled": "sk", "skilled_react": "react", "skilled_react_depth": "depth", "skilled_mobile": "mobile",
      "skilled_elastic": "elast", "skilled_herisson": "heris", "skilled_appat": "appat", "skilled_sortie": "sortie"}


def run_fixed(srv, seed, enemy, man="M3"):
    """Op a manoeuvre FIXE (le commandant tetu) — meme setup que l'officier, mais plan impose."""
    env, garrison, prof = officer_live.setup_op(srv, seed, enemy, lambda x: None)
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = garrison[0][2]
    r = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
    r.run(max_steps=500, max_wall=1200, stall_wall=500)
    return metrics_dyn(env, r, garrison)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=2)          # ops par posture et par condition
    p.add_argument("--servers", type=int, default=16)
    p.add_argument("--out", type=str, default="officer_vs_fixe.jsonl")
    a = p.parse_args()

    # jobs : pour chaque posture x rep -> 2 conditions (officier, M3-fixe), meme seed
    jobs = []
    for rep in range(a.reps):
        for pi, post in enumerate(POSTURES):
            seed = 100 + rep * 10 + pi
            jobs.append((seed, post, "officier"))
            jobs.append((seed, post, "fixe"))
    lock = threading.Lock(); cur = [0]; results = []
    print("=== MESURE 1.5 : %d ops (%d postures x %d reps x 2 conditions) sur %d serveurs ==="
          % (len(jobs), len(POSTURES), a.reps, a.servers), flush=True)

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                seed, post, cond = jobs[cur[0]]; cur[0] += 1
            t0 = time.time()
            try:
                if cond == "officier":
                    m = officer_live.run_officer_op(srv, seed, post, verbose=False)
                else:
                    m = run_fixed(srv, seed, post, "M3")
                rec = {"seed": seed, "posture": post, "cond": cond, "mil": bool(m["mil"]),
                       "pertes": round(m["pertes"], 2), "manoeuvre": m.get("manoeuvre", "M3"),
                       "redecision": m.get("redecision"), "dt": round(time.time() - t0, 0)}
            except Exception as e:
                rec = {"seed": seed, "posture": post, "cond": cond, "err": type(e).__name__}
            with lock:
                results.append(rec)
                with open(a.out, "a") as f: f.write(json.dumps(rec) + "\n")
                ok = [r for r in results if "mil" in r]
                no = sum(1 for r in ok if r["cond"] == "officier" and r["mil"]); nd = sum(1 for r in ok if r["cond"] == "officier")
                fo = sum(1 for r in ok if r["cond"] == "fixe" and r["mil"]); fd = sum(1 for r in ok if r["cond"] == "fixe")
                print("[%d/%d] srv%d %s/%s -> mil=%s (officier %d/%d, fixe %d/%d)"
                      % (len(results), len(jobs), srv, SH[post], cond, rec.get("mil"), no, nd, fo, fd), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()

    ok = [r for r in results if "mil" in r]
    off = [r for r in ok if r["cond"] == "officier"]; fix = [r for r in ok if r["cond"] == "fixe"]
    print("\n===== RESULTAT 1.5 =====", flush=True)
    print("OFFICIER adaptatif : %d/%d = %.0f%% succes" % (sum(r["mil"] for r in off), len(off), 100 * sum(r["mil"] for r in off) / max(1, len(off))))
    print("M3-FIXE (tetu)     : %d/%d = %.0f%% succes" % (sum(r["mil"] for r in fix), len(fix), 100 * sum(r["mil"] for r in fix) / max(1, len(fix))))
    print("\npar posture (officier vs fixe, succes) :")
    for post in POSTURES:
        o = [r["mil"] for r in off if r["posture"] == post]; f = [r["mil"] for r in fix if r["posture"] == post]
        print("  %-7s officier %d/%d | fixe %d/%d" % (SH[post], sum(o), len(o), sum(f), len(f)))
