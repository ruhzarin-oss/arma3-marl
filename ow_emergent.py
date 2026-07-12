#!/usr/bin/env python3
"""ow_emergent.py — LE TEST DECISIF (refute ou non 'la verticalite exige un corps physique').
Exposition EMERGENTE (fraction du corps touchable = geometrie, ZERO knob) vs baseline et LOS-2.5D-seul.
Cartes relief HELD-OUT, N seeds. Si 'emergent' >> baseline de facon robuste -> conclusion 4 REFUTEE."""
import sys, json, time, argparse, subprocess, statistics as st
HERE = "/home/younes/arma3-marl"; PY = HERE + "/.venv/bin/python"
ARMS = ["flat_none", "los25_none", "emergent"]
ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--P", type=int, default=3)
ap.add_argument("--ne", type=int, default=1024); ap.add_argument("--rounds", type=int, default=18)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--D", type=int, default=6)
ap.add_argument("--rspawn", type=float, default=90.0); ap.add_argument("--out", default=HERE + "/ow_emergent_results.txt")
a = ap.parse_args()

jobs = [(arm, sd) for arm in ARMS for sd in range(a.seeds)]
outs = {(arm, sd): "/tmp/owe_%s_%d.json" % (arm, sd) for (arm, sd) in jobs}
logf = open(a.out, "w")
def log(x): print(x, flush=True); logf.write(x + "\n"); logf.flush()

def cmd(arm, sd):
    return [PY, HERE + "/ow_worker.py", "--arm", arm, "--seed", str(sd), "--ne", str(a.ne),
            "--rounds", str(a.rounds), "--D", str(a.D), "--rspawn", str(a.rspawn),
            "--hit", str(a.hit), "--out", outs[(arm, sd)]]

t0 = time.time(); todo = list(jobs); running = []
log("=== TEST EMERGENT | %d jobs (%d bras x %d seeds), P=%d | ne=%d rounds=%d ===" % (len(jobs), len(ARMS), a.seeds, a.P, a.ne, a.rounds))
log("  TRAIN=ronda,matera,positano,sarajevo  TEST(held-out)=athens,delphi,santorini")
while todo or running:
    while todo and len(running) < a.P:
        arm, sd = todo.pop(0)
        p = subprocess.Popen(cmd(arm, sd), stdout=open("/tmp/owe_%s_%d.log" % (arm, sd), "w"), stderr=subprocess.STDOUT)
        running.append((p, arm, sd)); log("  lance %-11s/seed%d  (%.0fs)" % (arm, sd, time.time() - t0))
    time.sleep(5)
    for tup in running[:]:
        p, arm, sd = tup
        if p.poll() is not None:
            running.remove(tup); log("  FINI  %-11s/seed%d  %s  (%.0fs)" % (arm, sd, "OK" if p.returncode == 0 else "ECHEC", time.time() - t0))

agg = {arm: {} for arm in ARMS}
for (arm, sd), o in outs.items():
    try:
        d = json.load(open(o))
    except Exception as e:
        log("  !! JSON manquant %s/seed%d : %s" % (arm, sd, e)); continue
    for mp, r in d["results"].items():
        for k, v in r.items(): agg[arm].setdefault(k, []).append(v)

def ms(arm, k):
    v = agg[arm].get(k, [])
    return (st.mean(v), (st.pstdev(v) if len(v) > 1 else 0.0)) if v else (0.0, 0.0)
def mean(arm, k): return ms(arm, k)[0]

log("\n=== RESULTATS (%d seeds x 3 cartes held-out) ===" % a.seeds)
log("  %-11s | %-14s %-14s %-14s %-8s %-6s" % ("bras", "survie", "dkilled", "win", "expo", "post"))
for arm in ARMS:
    log("  %-11s | %5.3f+-%4.3f  %5.3f+-%4.3f  %5.3f+-%4.3f  %.3f  %.2f" %
        (arm, *ms(arm, "survie"), *ms(arm, "dkilled"), *ms(arm, "win"), mean(arm, "expo"), mean(arm, "posture")))

log("\n=== VERDICT (emergent - baseline flat_none) ===")
for k in ("win", "dkilled", "survie"):
    log("  %-8s : %+.3f" % (k, mean("emergent", k) - mean("flat_none", k)))
dW = mean("emergent", "win") - mean("flat_none", "win")
losW = mean("los25_none", "win") - mean("flat_none", "win")
log("  LOS 2.5D seul sur win : %+.3f  |  EMERGENT sur win : %+.3f" % (losW, dW))
log("  -> conclusion 4 (verticalite exige un corps physique) : %s" %
    ("REFUTEE (l'emergence fait payer la verticalite dans l'abstrait)" if dW > 0.08 else
     "NON refutee ici (meme emergent ne paie pas -> scenario statique trop faible, tester manoeuvre)"))
log("\ntotal %.1f min" % ((time.time() - t0) / 60))
