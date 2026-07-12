#!/usr/bin/env python3
"""ow_ablation.py — ablation OVERWATCH en PARALLELE (P sous-process partagent le GPU).
5 bras x N seeds. Entraine sur 4 cartes relief, evalue sur 3 HELD-OUT. Repond aux 3 questions :
  1) QUEL LEVIER : ablation 2x2 (LOS 2.5D x corps hull-down)
  2) ROBUSTESSE : seeds + cartes disjointes (train != test)
  3) HULL trop genereux ? : bras 'full_mild' (hull attenue 0.7/0.5) vs 'full' (0.5/0.2)"""
import sys, json, time, argparse, subprocess, statistics as st
HERE = "/home/younes/arma3-marl"; PY = HERE + "/.venv/bin/python"
TEST = ["athens", "delphi", "santorini"]
ARMS = ["flat_none", "los25_none", "flat_hull", "full", "full_mild"]
ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--P", type=int, default=3)
ap.add_argument("--ne", type=int, default=1024); ap.add_argument("--rounds", type=int, default=18)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--D", type=int, default=6)
ap.add_argument("--rspawn", type=float, default=90.0); ap.add_argument("--out", default=HERE + "/ow_ablation_results.txt")
a = ap.parse_args()

jobs = [(arm, sd) for arm in ARMS for sd in range(a.seeds)]
outs = {(arm, sd): "/tmp/oww_%s_%d.json" % (arm, sd) for (arm, sd) in jobs}
logf = open(a.out, "w")
def log(x): print(x, flush=True); logf.write(x + "\n"); logf.flush()

def cmd(arm, sd):
    return [PY, HERE + "/ow_worker.py", "--arm", arm, "--seed", str(sd), "--ne", str(a.ne),
            "--rounds", str(a.rounds), "--D", str(a.D), "--rspawn", str(a.rspawn),
            "--hit", str(a.hit), "--out", outs[(arm, sd)]]

t0 = time.time(); todo = list(jobs); running = []
log("=== ABLATION OVERWATCH | %d jobs (%d bras x %d seeds), P=%d | ne=%d rounds=%d hit=%.2f ===" %
    (len(jobs), len(ARMS), a.seeds, a.P, a.ne, a.rounds, a.hit))
log("  TRAIN=ronda,matera,positano,sarajevo  TEST(held-out)=athens,delphi,santorini")
while todo or running:
    while todo and len(running) < a.P:
        arm, sd = todo.pop(0)
        p = subprocess.Popen(cmd(arm, sd), stdout=open("/tmp/oww_%s_%d.log" % (arm, sd), "w"), stderr=subprocess.STDOUT)
        running.append((p, arm, sd)); log("  lance %-11s/seed%d  (%.0fs, %d en cours)" % (arm, sd, time.time() - t0, len(running)))
    time.sleep(5)
    for tup in running[:]:
        p, arm, sd = tup
        if p.poll() is not None:
            running.remove(tup)
            tag = "OK" if p.returncode == 0 else "ECHEC(%d)" % p.returncode
            log("  FINI  %-11s/seed%d  %s  (%.0fs)" % (arm, sd, tag, time.time() - t0))

agg = {arm: {} for arm in ARMS}
for (arm, sd), o in outs.items():
    try:
        d = json.load(open(o))
    except Exception as e:
        log("  !! JSON manquant %s/seed%d : %s (voir /tmp/oww_%s_%d.log)" % (arm, sd, e, arm, sd)); continue
    for mp, r in d["results"].items():
        for k, v in r.items(): agg[arm].setdefault(k, []).append(v)

def ms(arm, k):
    v = agg[arm].get(k, [])
    return (st.mean(v), (st.pstdev(v) if len(v) > 1 else 0.0)) if v else (0.0, 0.0)
def mean(arm, k): return ms(arm, k)[0]

log("\n=== RESULTATS PAR BRAS (moyenne +- ecart-type, %d seeds x 3 cartes held-out) ===" % a.seeds)
log("  %-11s | %-14s %-14s %-14s %-8s %-6s" % ("bras", "survie", "dkilled", "win", "expo", "post"))
for arm in ARMS:
    log("  %-11s | %5.3f+-%4.3f  %5.3f+-%4.3f  %5.3f+-%4.3f  %.3f  %.2f" %
        (arm, *ms(arm, "survie"), *ms(arm, "dkilled"), *ms(arm, "win"), mean(arm, "expo"), mean(arm, "posture")))

log("\n=== ABLATION 2x2 (effet sur WIN = objectif atteint) ===")
b = lambda arm: mean(arm, "win")
los = b("los25_none") - b("flat_none"); hull = b("flat_hull") - b("flat_none")
comb = b("full") - b("flat_none"); inter = b("full") - b("los25_none") - b("flat_hull") + b("flat_none")
log("  LOS 2.5D seul   (los25_none - flat_none) : %+.3f" % los)
log("  hull-down seul  (flat_hull  - flat_none) : %+.3f" % hull)
log("  les deux        (full       - flat_none) : %+.3f" % comb)
log("  INTERACTION     (synergie au-dela de l'addition) : %+.3f" % inter)
verdict = "hull-down" if hull > los + 0.05 else ("LOS 2.5D" if los > hull + 0.05 else "les DEUX a parts ~egales")
log("  -> levier dominant : %s" % verdict)

log("\n=== HULL trop genereux ? (full 0.5/0.2  vs  full_mild 0.7/0.5) ===")
log("  survie : full=%.3f  full_mild=%.3f  (delta %+.3f)" % (mean("full", "survie"), mean("full_mild", "survie"), mean("full_mild", "survie") - mean("full", "survie")))
log("  win    : full=%.3f  full_mild=%.3f  (delta %+.3f)" % (mean("full", "win"), mean("full_mild", "win"), mean("full_mild", "win") - mean("full", "win")))
rob = mean("full_mild", "win") - b("flat_none")
log("  -> meme avec hull ATTENUE, l'avantage vs baseline tient : %s (win %+.3f)" % ("OUI" if rob > 0.10 else "FRAGILE", rob))
log("\ntotal %.1f min" % ((time.time() - t0) / 60))
