import sys
sys.path.insert(0, "/home/younes/arma3-marl")
from train_soldier import run

# Cherche la bande de difficulte ou la COQUE fait la difference (entre plancher et plafond).
ITERS, ENVS = 150, 8192
CONFIGS = [(2, 0.13), (3, 0.12), (3, 0.15), (2, 0.16)]   # (D defenseurs, hit letalite)
print("=== SWEEP difficulte : Δ max coque-vs-sans ===", flush=True)
best = None
for D, hit in CONFIGS:
    rs, ls = run(True,  ITERS, ENVS, 1, D, 40.0, hit, 0, tag="sw_s")
    rb, lb = run(False, ITERS, ENVS, 1, D, 40.0, hit, 0, tag="sw_n")
    gap = 100 * (rs - rb)
    print(">>> D=%d hit=%.2f : COQUE %.0f%% (p%.0f) | SANS %.0f%% (p%.0f) | ecart %+.0f"
          % (D, hit, 100*rs, 100*ls, 100*rb, 100*lb, gap), flush=True)
    if best is None or gap > best[0]:
        best = (gap, D, hit)
print(">>> MEILLEUR : ecart %+.0f a D=%d hit=%.2f" % best, flush=True)
print("SWEEP FINI", flush=True)
