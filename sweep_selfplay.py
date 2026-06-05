"""Sweep self-play : balaie la letalite (hit) pour trouver la config la plus DECISIVE tout en restant equilibree."""
from train_selfplay import train
print("=== SWEEP SELF-PLAY (letalite) ===")
best = None
for hit in [0.16, 0.24, 0.32, 0.42]:
    w0, w1, dr = train(iters=280, hit=hit, secn=2)
    bal = 1.0 - abs(w0 - w1)  # 1 = parfait equilibre
    score = dr * bal          # decisif ET equilibre
    print("hit=%.2f -> BLU %.2f / OPF %.2f | decidees %.2f | equilibre %.2f | SCORE %.3f" % (hit, w0, w1, dr, bal, score))
    if best is None or score > best[0]:
        best = (score, hit, dr, bal)
print("=== MEILLEUR : hit=%.2f (decidees %.2f, equilibre %.2f) ===" % (best[1], best[2], best[3]))
