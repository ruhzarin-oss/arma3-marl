import sys, glob, os, statistics
sys.path.insert(0, "/mnt/c/Users/Younes"); sys.path.insert(0, "/mnt/data/hmt/depot")
from alize_bruit import lire, position_a
d_all, d300 = [], []
for ep in sorted(glob.glob("/mnt/data/hmt/runs/*_alize1_i*/g*_r*")):
    if not os.path.exists(f"{ep}/extrait/etat.csv"): continue
    fs, ev, froles, tirs, pos, ticks = lire(ep)
    premier = {}
    for te, typ, i, sx, sy, tot in ev:
        if typ == "C" and i not in premier: premier[i] = te
    for i, tc in premier.items():
        # debut de la rafale : premier coup ennemi d une suite sans trou de plus de 5 s qui finit au coup recu
        avant = sorted(t for t, tireur in tirs if t < tc - 0.05)
        if not avant: d_all.append(None); continue
        debut = avant[-1]
        for t in reversed(avant[:-1]):
            if debut - t <= 5: debut = t
            else: break
        d_all.append(tc - debut)
v = [x for x in d_all if x is not None]
print(f"hommes touches {len(d_all)} ; sans aucun coup ennemi avant : {d_all.count(None)}")
print(f"delai entre le DEBUT de la rafale ennemie et le coup recu : mediane {statistics.median(v):.1f} s ; quartiles {statistics.quantiles(v, n=4)} ; moins de 2 s : {sum(1 for x in v if x < 2)} ; moins de 5 s : {sum(1 for x in v if x < 5)}")
