"""collect_geo_recon — LA GEOMETRIE EST-ELLE LISIBLE ? (la ou le COMPORTEMENT echouait a 26-32%).
On lit les positions ennemies au spawn (lecture COMPLETE = borne haute : si ca echoue meme la, c'est mort),
on extrait des features SPATIALES, on classe la geometrie parmi 5. LOO plus-proche-centroide."""
import argparse, threading, json
import numpy as np
from op_arma import OpArma
from enemy_profiles import apply_profile, PRO_SKILL_SQF
from geometries import GEOMETRIES, OBJ
import maneuvers as M

SB = "/mnt/data/harmattan-sandbox"
GEOS = ["standard", "concentre", "disperse", "faible_ouest", "faible_est"]
SH = {"standard": "std", "concentre": "conc", "disperse": "disp", "faible_ouest": "f_O", "faible_est": "f_E"}
FEATS = ["disp", "sx", "sy", "n_core", "n_w", "n_e", "n_n", "maxd"]


def setup_geo(srv, seed, geo):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=M.SQUADS, mission=mis, log=log, move=36, seed=seed)
    garrison, prof = apply_profile(env, "skilled", GEOMETRIES[geo])
    env.spawn(M.SPAWNS, garrison)
    env.b.send(PRO_SKILL_SQF, wait=True)
    return env


def geo_features(env):
    env.read(); env.read()
    al = env.en_alive(); gx, gy = OBJ
    ex, ey = env.epx[al], env.epy[al]
    if len(ex) == 0:
        return None
    d = np.sqrt((ex - gx) ** 2 + (ey - gy) ** 2)
    return {"disp": float(d.mean()), "sx": float(ex.std()), "sy": float(ey.std()),
            "n_core": int((d < 50).sum()), "n_w": int((ex < gx - 60).sum()), "n_e": int((ex > gx + 60).sum()),
            "n_n": int((ey > gy + 60).sum()), "maxd": float(d.max()), "n": int(al.sum())}


def run_one(srv, seed, geo):
    return geo_features(setup_geo(srv, seed, geo))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=20); p.add_argument("--servers", type=int, default=16)
    p.add_argument("--out", type=str, default="geo_recon.jsonl")
    a = p.parse_args()
    jobs = [(700 + rep * 5 + gi, GEOS[gi]) for rep in range(a.reps) for gi in range(len(GEOS))]
    open(a.out, "w").close()
    lock = threading.Lock(); cur = [0]; done = [0]
    print("=== GEO-RECON : %d spawns (%d geo x %d reps) ===" % (len(jobs), len(GEOS), a.reps), flush=True)

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                seed, geo = jobs[cur[0]]; cur[0] += 1
            try:
                f = run_one(srv, seed, geo)
                rec = {"geo": geo, **f} if f else {"geo": geo, "err": "no_enemy"}
            except Exception as e:
                rec = {"geo": geo, "err": type(e).__name__ + ":" + str(e)[:60]}
            with lock:
                with open(a.out, "a") as fh: fh.write(json.dumps(rec) + "\n")
                done[0] += 1
                print("[%d/%d] %s" % (done[0], len(jobs), rec.get("geo")), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()
    analyse(a.out)


def analyse(path):
    rows = [json.loads(l) for l in open(path)]
    ok = [r for r in rows if "disp" in r]; err = [r for r in rows if "err" in r]
    print("\n===== GEOMETRIE LISIBLE ? (%d valides, %d err) =====" % (len(ok), len(err)), flush=True)
    if len(ok) < 10:
        print("trop peu."); return
    X = np.array([[float(r[k]) for k in FEATS] for r in ok]); y = np.array([r["geo"] for r in ok])
    print("\n-- moyennes par geometrie --")
    print("%-6s " % "geo" + " ".join("%6s" % k for k in FEATS))
    for g in GEOS:
        print("%-6s " % SH[g] + " ".join("%6.1f" % (X[y == g, j].mean() if (y == g).any() else float("nan")) for j, k in enumerate(FEATS)))
    mu = X.mean(0); sd = X.std(0) + 1e-9; Z = (X - mu) / sd
    correct = 0; conf = {g: {h: 0 for h in GEOS} for g in GEOS}
    for i in range(len(Z)):
        mask = np.ones(len(Z), bool); mask[i] = False
        cents = {g: Z[mask & (y == g)].mean(0) for g in GEOS if (mask & (y == g)).any()}
        pred = min(cents, key=lambda g: np.linalg.norm(Z[i] - cents[g]))
        conf[y[i]][pred] += 1; correct += (pred == y[i])
    acc = 100 * correct / len(Z)
    print("\n-- LOO plus-proche-centroide : %.0f%% (hasard 20%%) --" % acc)
    print("%-6s |" % "vrai" + " ".join("%5s" % SH[g] for g in GEOS))
    for g in GEOS:
        print("%-6s |" % SH[g] + " ".join("%5d" % conf[g][h] for h in GEOS))
    print("\nVERDICT : %s" % ("GEOMETRIE LISIBLE -> boucle adaptative viable" if acc >= 80
          else "partiellement lisible" if acc >= 55 else "illisible aussi -> reflechir"))


if __name__ == "__main__":
    main()
