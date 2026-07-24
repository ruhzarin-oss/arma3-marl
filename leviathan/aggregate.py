#!/usr/bin/env python3
"""aggregate.py — agrège K runs par mode -> stats (taux de prise, pertes moyennes...) + choisit un run
REPRÉSENTATIF (médiane des pertes) pour l'affichage. Écrit ab_frontal.json / ab_envelop.json pour build_ab."""
import json, glob, statistics

BASE = "/home/younes/arma3-marl/leviathan/"


def agg(mode):
    files = sorted(glob.glob(BASE + "ab_%s_*.json" % mode))
    runs = [(f, json.load(open(f))) for f in files]
    M = [d["metrics"] for _, d in runs]
    K = len(M)
    if K == 0:
        print("%s: AUCUN run" % mode); return
    took = sum(1 for m in M if m["took"])
    wl = [m["west_losses"] for m in M]; ek = [m["east_neutralized"] for m in M]; md = [m["min_fob_dist"] for m in M]
    a = {"mode": mode, "runs": K, "nag": M[0]["nag"], "east_start": round(statistics.mean(m["east_start"] for m in M)),
         "took_rate": took / K, "took": took > K / 2,
         "west_losses_mean": round(statistics.mean(wl), 1), "east_neutralized_mean": round(statistics.mean(ek), 1),
         "min_fob_dist_mean": round(statistics.mean(md)),
         # champs bruts (compat build_ab) = les moyennes
         "west_losses": round(statistics.mean(wl), 1), "east_neutralized": round(statistics.mean(ek), 1), "min_fob_dist": round(statistics.mean(md))}
    med = statistics.median(wl)
    rep = min(runs, key=lambda r: abs(r[1]["metrics"]["west_losses"] - med))   # run représentatif = pertes ~ médiane
    repd = rep[1]; repd["metrics"] = {**repd["metrics"], **a}
    json.dump(repd, open(BASE + "ab_%s.json" % mode, "w"))
    print("%-8s | %d runs | FOB pris %d/%d (%.0f%%) | pertes WEST moy %.1f/%d | EAST neutr moy %.1f/%d | dist min moy %dm | rep=%s" % (
        mode, K, took, K, 100 * took / K, a["west_losses_mean"], a["nag"], a["east_neutralized_mean"], a["east_start"], a["min_fob_dist_mean"], rep[0].split("/")[-1]))
    return a


import sys
modes = sys.argv[1:] if len(sys.argv) > 1 else ["frontal", "envelop"]
for m in modes:
    agg(m)
print("AGG_DONE")
