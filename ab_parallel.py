#!/usr/bin/env python3
"""ab_parallel.py — lance l'A/B en PARALLELE : P sous-processus concurrents partagent le GPU.
Chaque (bras, seed) = un ab_worker.py isole (safe pour CUDA). Puis agrege + verdict.
VRAM : chaque process ~peak(ne). A ne=1024, ~5 Go/process -> P=3-4 tient sur 24 Go.
Pour du vrai partage GPU, activer NVIDIA MPS (sinon time-slicing, marche quand meme)."""
import sys, json, time, argparse, subprocess, statistics as st
HERE = "/home/younes/arma3-marl"; PY = HERE + "/.venv/bin/python"
TEST_FLAT = ["newyork", "london", "lille"]; TEST_RELIEF = ["athens", "delphi", "santorini"]
ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=5); ap.add_argument("--P", type=int, default=3)
ap.add_argument("--ne", type=int, default=1024); ap.add_argument("--rounds", type=int, default=20)
ap.add_argument("--K", type=int, default=4); ap.add_argument("--A", type=int, default=9)
ap.add_argument("--D", type=int, default=6); ap.add_argument("--rspawn", type=float, default=60.0)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--out", default=HERE + "/ab_parallel_results.txt")
a = ap.parse_args()

jobs = [(arm, sd) for arm in ("A", "B") for sd in range(a.seeds)]
outs = {(arm, sd): "/tmp/abw_%s_%d.json" % (arm, sd) for (arm, sd) in jobs}
logf = open(a.out, "w")
def log(x): print(x, flush=True); logf.write(x + "\n"); logf.flush()

def cmd(arm, sd):
    return [PY, HERE + "/ab_worker.py", "--arm", arm, "--seed", str(sd), "--ne", str(a.ne),
            "--rounds", str(a.rounds), "--K", str(a.K), "--A", str(a.A), "--D", str(a.D),
            "--rspawn", str(a.rspawn), "--hit", str(a.hit), "--out", outs[(arm, sd)]]

t0 = time.time(); todo = list(jobs); running = []
log("=== A/B PARALLELE | %d jobs, P=%d | ne=%d rounds=%d hit=%.2f D=%d rspawn=%.0f ===" %
    (len(jobs), a.P, a.ne, a.rounds, a.hit, a.D, a.rspawn))
while todo or running:
    while todo and len(running) < a.P:
        arm, sd = todo.pop(0)
        p = subprocess.Popen(cmd(arm, sd), stdout=open("/tmp/abw_%s_%d.log" % (arm, sd), "w"), stderr=subprocess.STDOUT)
        running.append((p, arm, sd)); log("  lance %s/seed%d  (%.0fs, %d/%d en cours)" % (arm, sd, time.time() - t0, len(running), a.P))
    time.sleep(5)
    for tup in running[:]:
        p, arm, sd = tup
        if p.poll() is not None:
            running.remove(tup); log("  FINI  %s/seed%d  code %d  (%.0fs)" % (arm, sd, p.returncode, time.time() - t0))

agg = {"A": {}, "B": {}}
for (arm, sd), o in outs.items():
    try:
        d = json.load(open(o))
    except Exception as e:
        log("  !! JSON manquant %s/seed%d : %s (voir /tmp/abw_%s_%d.log)" % (arm, sd, e, arm, sd)); continue
    for mp, r in d["results"].items():
        agg[arm].setdefault(mp, {k: [] for k in r})
        for k, v in r.items(): agg[arm][mp][k].append(v)

def pool(arm, maps, k): return [x for mp in maps for x in agg[arm].get(mp, {}).get(k, [])]
def ms(v): return (st.mean(v), (st.pstdev(v) if len(v) > 1 else 0.0)) if v else (0.0, 0.0)
log("\n=== RESULTATS (%d seeds) ===" % a.seeds)
for cat, maps in (("PLAT", TEST_FLAT), ("RELIEF", TEST_RELIEF)):
    log("--- TEST %s ---" % cat)
    for k in ("survie", "expo", "dkilled", "win"):
        (ma, sa), (mb, sb) = ms(pool("A", maps, k)), ms(pool("B", maps, k))
        log("  %-8s : A=%.3f+-%.3f  B=%.3f+-%.3f  delta=%+.3f" % (k, ma, sa, mb, sb, mb - ma))
    pu = pool("B", maps, "posture"); log("  usage postures (B) : %.2f" % (st.mean(pu) if pu else 0))
allm = TEST_FLAT + TEST_RELIEF
dS = st.mean(pool("B", allm, "survie") or [0]) - st.mean(pool("A", allm, "survie") or [0])
gk = st.mean(pool("B", allm, "dkilled") or [0]) >= st.mean(pool("A", allm, "dkilled") or [0])
ex = st.mean(pool("B", allm, "expo") or [1]) < st.mean(pool("A", allm, "expo") or [0])
log("\n=== VERDICT ===")
log("  survie(B-A)=%+.3f (>=+0.10): %s | garde-fou dkilled: %s | expo(B)<expo(A): %s" %
    (dS, "OUI" if dS >= 0.10 else "non", "OUI" if gk else "NON", "OUI" if ex else "non"))
log("  -> H1 %s" % ("CONFIRMEE" if (dS >= 0.10 and gk and ex) else "non confirmee"))
log("total %.1f min" % ((time.time() - t0) / 60))
