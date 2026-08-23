#!/usr/bin/env python3
"""LE NATIF SUR LE BANC REPARE — deux passes, lecteur DEPOSE, rien d autre ne change.

Predicat `DEPOT_NATIF.md` (16/08) : deux passes, concordance exigee a moins de 10 points,
sinon aucun des deux ne se cite. Conditions eliminatoires : prevol vert, le monde bouge
(> 1 m/pas), le natif tire.
"""
import glob, math, collections, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

res = {}
for pas in ("p1", "p2"):
    E = [e for e in (LN.lire(f) for f in sorted(glob.glob("/mnt/data/natif2/%s_e*.txt" % pas))) if e]
    c = collections.Counter(e["etat"] for e in E)
    ok = [e for e in E if e["etat"] == "ok"]
    mp = sorted(e["mpas"] for e in ok); med = mp[len(mp)//2] if mp else 0.0
    bouge = ok if med > 1.0 else []
    print("\n=== %s ===  %d episodes complets" % (pas.upper(), len(E)))
    for k, v in sorted(c.items()): print("   %-16s %d" % (k, v))
    print("   condition 2 · le monde bouge : mediane %.2f m/pas -> %s"
          % (med, "PASSE" if med > 1.0 else "⛔ LE MONDE NE BOUGE PAS"))
    cps = sorted(e["coups"] for e in ok if e["coups"] >= 0)
    if cps: print("   condition 3 · coups attaquants : mediane %d" % cps[len(cps)//2])
    res[pas] = bouge
    if bouge:
        pr = sum(1 for e in bouge if e["prise"])
        print("   ➤ PRISES : %d / %d = %.1f %%" % (pr, len(bouge), 100.0*pr/len(bouge)))

a, b = res["p1"], res["p2"]
if a and b:
    ta = 100.0*sum(1 for e in a if e["prise"])/len(a)
    tb = 100.0*sum(1 for e in b if e["prise"])/len(b)
    print("\n═══ CONCORDANCE — critere depose : moins de 10 points ═══")
    print("  passe 1 : %.1f %% (n=%d)   passe 2 : %.1f %% (n=%d)   ecart : %.1f points"
          % (ta, len(a), tb, len(b), abs(ta-tb)))
    print("  %s" % ("✓ CONCORDANT" if abs(ta-tb) < 10 else "⛔ DISCORDANT — aucun des deux ne se cite"))
    if abs(ta-tb) < 10:
        tot = a + b; n = len(tot); k = sum(1 for e in tot if e["prise"]); p = k/n
        ic = 1.96*math.sqrt(p*(1-p)/n)
        print("\n  ➤ NATIF (banc repare) = %.1f %%   n=%d   IC95 [%.1f ; %.1f]"
              % (100*p, n, 100*(p-ic), 100*(p+ic)))
        print("     pour memoire, meme bras sur le banc CASSE : 59,6 %%  n=114")
