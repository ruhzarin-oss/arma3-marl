import sys, glob, os, re, statistics
sys.path.insert(0, "/mnt/c/Users/Younes"); sys.path.insert(0, "/mnt/data/hmt/depot")
from alize_bruit import lire
# ! Fable 11/09 : la balle qui touche a sa propre ligne tir 0,1-0,4 s avant le Hit. On l exclut : le tir
# du tireur du coup_recu dans [tc - 1 s, tc]. La rafale = suite de coups ennemis sans trou de plus de 5 s.
d_all = []
for ep in sorted(glob.glob("/mnt/data/hmt/runs/*_alize1_i*/g*_r*")):
    if not os.path.exists(f"{ep}/extrait/etat.csv"): continue
    fs, ev, froles, tirs, pos, ticks = lire(ep)
    rpt = open(f"{ep}/serveur.rpt", errors="ignore").read()
    tireur_du_coup = {}
    for m in re.finditer(r'CHACAL\|E\|coup_recu\|([0-9.]+)\|(\d+)\|(-?\d+)\|', rpt):
        tireur_du_coup.setdefault(int(m.group(2)), (float(m.group(1)), int(m.group(3))))
    for i, (tc, src) in tireur_du_coup.items():
        if i not in fs: continue
        avant = sorted(t for t, tireur in tirs if t < tc and not (tireur == src and t >= tc - 1.0))
        if not avant: d_all.append(None); continue
        debut = avant[-1]
        for t in reversed(avant[:-1]):
            if debut - t <= 5: debut = t
            else: break
        d_all.append(tc - debut if tc - avant[-1] <= 5 else None)
v = [x for x in d_all if x is not None]
print(f"hommes touches {len(d_all)} ; sans rafale ennemie dans les 5 s avant (hors balle qui touche) : {d_all.count(None)}")
print(f"delai debut de rafale -> coup : mediane {statistics.median(v):.1f} s ; quartiles {[round(q,1) for q in statistics.quantiles(v, n=4)]} ; < 2 s : {sum(1 for x in v if x < 2)} ; < 5 s : {sum(1 for x in v if x < 5)} (sur {len(v)})")
