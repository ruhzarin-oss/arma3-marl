"""collect_trace — PIVOT adaptation-au-contact, etape DONNEES : on joue un assaut M3 reel contre chaque
posture et on TRACE pas-a-pas le comportement ennemi (qui tient l'objectif, qui vient vers nous, qui
decroche). But : trouver A QUEL MOMENT et PAR QUEL signal la posture se revele PENDANT le combat
(la sonde a froid donnait 26% = hasard ; ici on teste si le COMBAT, lui, separe les postures)."""
import argparse, threading, json
import numpy as np, torch
import officer_live
from train_koth_gpu import Net
from op_arma import OperationRunner
import maneuvers as M
from enemy_profiles import metrics_dyn

DEV = "cuda:0"
POSTURES = officer_live.POSTURES
LABEL = {"skilled": "M3", "skilled_react": "M3", "skilled_react_depth": "M3", "skilled_mobile": "M3",
         "skilled_elastic": "M1", "skilled_herisson": "M8", "skilled_appat": "M12", "skilled_sortie": "M12"}
SH = {"skilled": "sk", "skilled_react": "react", "skilled_react_depth": "depth", "skilled_mobile": "mobile",
      "skilled_elastic": "elast", "skilled_herisson": "heris", "skilled_appat": "appat", "skilled_sortie": "sortie"}


def snapshot(r):
    env = r.env; al = env.en_alive(); gx, gy = env.base
    our = sum(int(env.alive(si).sum()) for si in range(env.S))
    # distance de NOS unites a l'objectif (progression de l'assaut)
    od = []
    for si in range(env.S):
        a = env.alive(si)
        if a.any(): od.append(float(np.sqrt((env.px[si][a] - gx) ** 2 + (env.py[si][a] - gy) ** 2).mean()))
    our_dist = round(float(np.mean(od)), 0) if od else 0.0
    if not al.any():
        return {"t": r.step_i, "en": 0, "our": our, "obj_hold": 0, "core_n": 0, "core_disp": 0.0,
                "toward": 0, "cy": 0.0, "our_dist": our_dist}
    ex, ey = env.epx[al], env.epy[al]; d = np.sqrt((ex - gx) ** 2 + (ey - gy) ** 2); core = d < 120
    return {"t": r.step_i, "en": int(al.sum()), "our": our,
            "obj_hold": int((d < 40).sum()),                 # qui tient l'objectif (appat -> 0, herisson reste)
            "core_n": int(core.sum()), "core_disp": round(float(d[core].mean()), 1) if core.any() else 0.0,
            "toward": int((ey < gy - 15).sum()),             # vient vers nous (sortie)
            "cy": round(float(ey.mean() - gy), 1),           # +nord (decroche/appat) / -sud (vers nous)
            "our_dist": our_dist}


def run_m3_traced(srv, seed, enemy):
    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env, garrison, prof = officer_live.setup_op(srv, seed, enemy)
    plan = M.MANEUVERS["M3"](qrf="inf"); plan["garr_n"] = garrison[0][2]
    r = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
    series = []
    r.run(max_steps=500, max_wall=1200, stall_wall=500, trace=lambda rr: series.append(snapshot(rr)))
    m = metrics_dyn(env, r, garrison)
    return series, bool(m["mil"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=5)
    p.add_argument("--servers", type=int, default=16)
    p.add_argument("--out", type=str, default="recon_trace.jsonl")
    a = p.parse_args()
    jobs = [(600 + rep * 8 + pi, POSTURES[pi]) for rep in range(a.reps) for pi in range(len(POSTURES))]
    open(a.out, "w").close()
    lock = threading.Lock(); cur = [0]; done = [0]
    print("=== TRACE : %d assauts M3 traces (%d postures x %d reps) sur %d serveurs ===" %
          (len(jobs), len(POSTURES), a.reps, a.servers), flush=True)

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                seed, post = jobs[cur[0]]; cur[0] += 1
            try:
                series, mil = run_m3_traced(srv, seed, post)
                rec = {"seed": seed, "posture": post, "label": LABEL[post], "mil": mil, "series": series}
            except Exception as e:
                rec = {"seed": seed, "posture": post, "err": type(e).__name__ + ":" + str(e)[:80]}
            with lock:
                with open(a.out, "a") as fh: fh.write(json.dumps(rec) + "\n")
                done[0] += 1
                print("[%d/%d] srv%d %s -> %s (%d pas)" % (done[0], len(jobs), srv, SH[post],
                      rec.get("label", "ERR"), len(rec.get("series", []))), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()
    analyse(a.out)


def analyse(path):
    rows = [json.loads(l) for l in open(path) if "err" not in json.loads(l)]
    print("\n===== TRACE : quand/comment la posture se revele =====", flush=True)
    if len(rows) < 8:
        print("trop peu de donnees."); return
    classes = ["M3", "M1", "M8", "M12"]
    # features AGREGEES sur le deroule du combat (pas une photo a froid)
    def feats(s):
        if not s: return None
        en0 = s[0]["en"] or 1
        obj = [x["obj_hold"] for x in s]; tw = [x["toward"] for x in s]; cy = [x["cy"] for x in s]
        # moment "contact mur" : 1er pas ou l'ennemi a perdu 40%
        kidx = next((i for i, x in enumerate(s) if x["en"] <= 0.6 * en0), len(s) - 1)
        tail = s[max(0, len(s) - 5):]                      # fin de combat
        return {
            "objhold_min": min(obj), "objhold_end": float(np.mean([x["obj_hold"] for x in tail])),
            "objhold_at_contact": s[kidx]["obj_hold"],
            "toward_max": max(tw), "toward_late": max(x["toward"] for x in tail),
            "cy_end": float(np.mean([x["cy"] for x in tail])), "cy_max": max(cy),
            "coredisp_end": float(np.mean([x["core_disp"] for x in tail])),
            "en_end": float(np.mean([x["en"] for x in tail])),
        }
    FK = ["objhold_min", "objhold_end", "objhold_at_contact", "toward_max", "toward_late",
          "cy_end", "cy_max", "coredisp_end", "en_end"]
    data = [(r["label"], feats(r["series"])) for r in rows if r.get("series")]
    data = [(lab, f) for lab, f in data if f]
    y = np.array([lab for lab, f in data]); X = np.array([[f[k] for k in FK] for lab, f in data])

    print("\n-- moyennes par classe (features du COMBAT) --")
    print("%-18s " % "feat" + " ".join("%8s" % c for c in classes))
    for j, k in enumerate(FK):
        print("%-18s " % k + " ".join("%8.1f" % (X[y == c, j].mean() if (y == c).any() else float("nan")) for c in classes))
    print("n par classe : " + " ".join("%s=%d" % (c, int((y == c).sum())) for c in classes))

    mu = X.mean(0); sd = X.std(0) + 1e-9; Z = (X - mu) / sd
    correct = 0; conf = {c: {d: 0 for d in classes} for c in classes}
    for i in range(len(Z)):
        mask = np.ones(len(Z), bool); mask[i] = False
        cents = {c: Z[mask & (y == c)].mean(0) for c in classes if (mask & (y == c)).any()}
        pred = min(cents, key=lambda c: np.linalg.norm(Z[i] - cents[c]))
        conf[y[i]][pred] += 1; correct += (pred == y[i])
    acc = 100 * correct / len(Z)
    print("\n-- LOO plus-proche-centroide (signal de COMBAT) : %.0f%% (hasard ~25%%) --" % acc)
    print("%-9s |" % "vrai\\pred" + " ".join("%5s" % c for c in classes))
    for c in classes:
        print("%-9s |" % c + " ".join("%5d" % conf[c][d] for d in classes))
    print("\nVERDICT : %s" % ("LE COMBAT REVELE LA POSTURE -> adaptation viable" if acc >= 60 else
          "signal de combat partiel" if acc >= 45 else "meme le combat ne separe pas nettement"), flush=True)


if __name__ == "__main__":
    main()
