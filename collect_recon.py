"""collect_recon v2 — OPTION 2 corrige par les diagnostics : on lit le COEUR (d<120, sans les patrouilles
statiques a ~180m qui noyaient le signal), avec une sonde DOUCE (pression de flanc, pas d'assaut qui detruit
le coeur) et une lecture PRECOCE (la fenetre est courte : le coeur fond en ~6 pas). On collecte n reps x 8
postures, puis on regarde si les 4 classes (M1/M3/M8/M12) se separent : moyennes par classe + LOO centroide."""
import argparse, threading, json
import numpy as np, torch
import officer_live
from train_koth_gpu import Net
import maneuvers as M

DEV = "cuda:0"
POSTURES = officer_live.POSTURES
LABEL = {"skilled": "M3", "skilled_react": "M3", "skilled_react_depth": "M3", "skilled_mobile": "M3",
         "skilled_elastic": "M1", "skilled_herisson": "M8", "skilled_appat": "M12", "skilled_sortie": "M12"}
SH = {"skilled": "sk", "skilled_react": "react", "skilled_react_depth": "depth", "skilled_mobile": "mobile",
      "skilled_elastic": "elast", "skilled_herisson": "heris", "skilled_appat": "appat", "skilled_sortie": "sortie"}

# features sur le COEUR (objectif conteste, d<120) — ce que verra le futur classifieur
FEATS = ["cn0", "cin0", "cdense0", "cdisp0", "cdrop", "cin1", "cdisp1", "ctoward_mx", "cnorth_mx", "cdy", "ourloss"]


def evec(env):
    """Photo du COEUR ennemi (d<120 de l'objectif ; exclut les patrouilles statiques). sud=vers nous."""
    al = env.en_alive()
    if env.en_n == 0 or not al.any():
        return None
    gx, gy = env.base
    ex, ey = env.epx[al], env.epy[al]
    d = np.sqrt((ex - gx) ** 2 + (ey - gy) ** 2)
    core = d < 120
    if not core.any():
        return {"cn": 0, "cin": 0, "cdisp": 0.0, "ccy": 0.0, "ctoward": 0, "cnorth": 0}
    dc = d[core]; eyc = ey[core]
    return {"cn": int(core.sum()), "cin": int((dc < 40).sum()), "cdisp": float(dc.mean()),
            "ccy": float(eyc.mean() - gy), "ctoward": int((eyc < gy - 15).sum()), "cnorth": int((eyc > gy + 15).sum())}


def our_alive(env):
    return int(sum(int(env.alive(si).sum()) for si in range(env.S)))


def _steps(env, brain, n):
    for _ in range(n):
        env.step([officer_live._act(env, brain, si) for si in range(env.S)])


def strong_probe(env, brain):
    # 1) SETTLE court : l'ennemi se met en posture (lecture precoce, avant que le coeur ne fonde)
    for si in range(env.S):
        env.stances[si] = "hold"
    _steps(env, brain, 6)
    s0 = evec(env); our0 = our_alive(env); cn0 = s0["cn"] if s0 else 0
    # 2) PRESSION DE FLANC douce (suppress depuis la crete + manoeuvre de flanc) — PAS d'assaut dans l'objectif
    push = {"SQ_APPUI": (M.CRETE, "suppress"), "SQ_A_OUEST": (M.FLANC_O, "move"),
            "SQ_A_EST": (M.LIGNE_E, "move"), "SQ_RESERVE": (M.POSTE_RES, "hold")}
    for sq, (g, st) in push.items():
        si = env.squads.index(sq); env.goals[si] = np.array(g, float); env.stances[si] = st
    _steps(env, brain, 5)
    s1 = evec(env)
    _steps(env, brain, 7)
    s2 = evec(env); ourN = our_alive(env)

    snaps = [s for s in (s0, s1, s2) if s] or [{"cn": 0, "cin": 0, "cdisp": 0.0, "ccy": 0.0, "ctoward": 0, "cnorth": 0}]
    s0 = s0 or snaps[0]; se = snaps[-1]
    return {
        "cn0": s0["cn"], "cin0": s0["cin"], "cdense0": round(s0["cin"] / max(1, s0["cn"]), 2),
        "cdisp0": round(s0["cdisp"], 1), "cdrop": s0["cn"] - se["cn"], "cin1": se["cin"],
        "cdisp1": round(se["cdisp"], 1), "ctoward_mx": max(s["ctoward"] for s in snaps),
        "cnorth_mx": max(s["cnorth"] for s in snaps), "cdy": round(se["ccy"] - s0["ccy"], 1),
        "ourloss": round(1 - ourN / max(1, our0), 3),
    }


def run_probe(srv, seed, enemy):
    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env, garrison, prof = officer_live.setup_op(srv, seed, enemy)
    return strong_probe(env, brain)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=12)
    p.add_argument("--servers", type=int, default=16)
    p.add_argument("--out", type=str, default="recon_features.jsonl")
    a = p.parse_args()
    jobs = [(500 + rep * 8 + pi, POSTURES[pi]) for rep in range(a.reps) for pi in range(len(POSTURES))]
    open(a.out, "w").close()
    lock = threading.Lock(); cur = [0]; done = [0]
    print("=== COLLECTE v2 (coeur) : %d sondes (%d postures x %d reps) sur %d serveurs ===" %
          (len(jobs), len(POSTURES), a.reps, a.servers), flush=True)

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                seed, post = jobs[cur[0]]; cur[0] += 1
            try:
                f = run_probe(srv, seed, post)
                rec = {"seed": seed, "posture": post, "label": LABEL[post], **f}
            except Exception as e:
                rec = {"seed": seed, "posture": post, "err": type(e).__name__ + ":" + str(e)[:80]}
            with lock:
                with open(a.out, "a") as fh: fh.write(json.dumps(rec) + "\n")
                done[0] += 1
                print("[%d/%d] srv%d %s -> %s" % (done[0], len(jobs), srv, SH[post],
                      rec.get("label", "ERR") if "err" not in rec else rec["err"]), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()
    analyse(a.out)


def analyse(path):
    rows = [json.loads(l) for l in open(path)]
    ok = [r for r in rows if "err" not in r]; err = [r for r in rows if "err" in r]
    print("\n===== SEPARABILITE v2 (%d sondes valides, %d erreurs) =====" % (len(ok), len(err)), flush=True)
    if len(ok) < 8:
        print("trop peu de donnees."); return
    classes = ["M3", "M1", "M8", "M12"]
    X = np.array([[float(r[k]) for k in FEATS] for r in ok]); y = np.array([r["label"] for r in ok])
    mu = X.mean(0); sd = X.std(0) + 1e-9; Z = (X - mu) / sd

    print("\n-- moyennes par classe (cible = manoeuvre ; coeur d<120) --")
    print("%-11s " % "feat" + " ".join("%8s" % c for c in classes))
    for j, k in enumerate(FEATS):
        print("%-11s " % k + " ".join("%8.1f" % (X[y == c, j].mean() if (y == c).any() else float("nan")) for c in classes))
    print("n par classe : " + " ".join("%s=%d" % (c, int((y == c).sum())) for c in classes))

    correct = 0; conf = {c: {d: 0 for d in classes} for c in classes}
    for i in range(len(Z)):
        mask = np.ones(len(Z), bool); mask[i] = False
        cents = {c: Z[mask & (y == c)].mean(0) for c in classes if (mask & (y == c)).any()}
        pred = min(cents, key=lambda c: np.linalg.norm(Z[i] - cents[c]))
        conf[y[i]][pred] += 1; correct += (pred == y[i])
    acc = 100 * correct / len(Z)
    print("\n-- LOO plus-proche-centroide : %.0f%% (hasard ~25%%) --" % acc)
    print("%-9s |" % "vrai\\pred" + " ".join("%5s" % c for c in classes))
    for c in classes:
        print("%-9s |" % c + " ".join("%5d" % conf[c][d] for d in classes))
    print("\nVERDICT : %s" % ("SEPARABLE -> classifieur OK" if acc >= 70 else
          "PARTIEL -> renforcable" if acc >= 50 else "FAIBLE -> recon a froid insuffisante"), flush=True)


if __name__ == "__main__":
    main()
