#!/usr/bin/env python3
"""rings_agg.py — agrège les anneaux (taux d'échange par distance) sur les K runs de chaque mode -> petit JSON."""
import json, glob, statistics
BASE = "/home/younes/arma3-marl/leviathan/"


def agg(mode):
    files = sorted(glob.glob(BASE + "ab_%s_*.json" % mode))
    runs = [json.load(open(f)) for f in files]
    K = len(runs); M = [d["metrics"] for d in runs]
    ring = {}
    for m in M:
        for r in m.get("rings", []):
            x = ring.setdefault(r["ring"], [0, 0]); x[0] += r["west"]; x[1] += r["east"]
    rings = [{"ring": b, "west": v[0], "east": v[1]} for b, v in sorted(ring.items())]
    took = sum(1 for m in M if m["took"])
    return {"mode": mode, "runs": K, "took_n": took, "took_rate": took / K, "nag": M[0]["nag"],
            "west_losses_mean": round(statistics.mean(m["west_losses"] for m in M), 1),
            "east_neutralized_mean": round(statistics.mean(m["east_neutralized"] for m in M), 1),
            "min_fob_dist_mean": round(statistics.mean(m["min_fob_dist"] for m in M)),
            "smoke_grenades": M[0].get("smoke_grenades", 0), "rings": rings}


out = {"timid": agg("timid"), "reckless": agg("reckless")}
json.dump(out, open(BASE + "rings_summary.json", "w"))
print(json.dumps(out, indent=0))
