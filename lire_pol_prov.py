#!/usr/bin/env python3
"""POLITIQUE, banc repare, passe 1 — ⚠️ PROVISOIRE : une passe ne se cite pas.
Le predicat exige deux passes concordantes a moins de 10 points. Lecteur DEPOSE, inchange.
"""
import glob, collections, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN
E = [e for e in (LN.lire(f) for f in sorted(glob.glob("/mnt/data/politique2/p1_e*.txt"))) if e]
c = collections.Counter(e["etat"] for e in E)
ok = [e for e in E if e["etat"] == "ok"]
mp = sorted(e["mpas"] for e in ok); med = mp[len(mp)//2] if mp else 0.0
print("\n  ══ POLITIQUE, banc repare, passe 1 — PROVISOIRE ══")
print("  episodes complets : %d" % len(E))
for k, v in sorted(c.items()): print("    %-16s %d" % (k, v))
print("  condition 2 · le monde bouge : mediane %.2f m/pas -> %s"
      % (med, "PASSE" if med > 1.0 else "⛔ NON"))
cps = sorted(e["coups"] for e in ok if e["coups"] >= 0)
if cps: print("  condition 3 · coups attaquants : mediane %d" % cps[len(cps)//2])
if ok and med > 1.0:
    pr = sum(1 for e in ok if e["prise"])
    print("\n  ➤ PRISES : %d / %d = %.1f %%   ⚠️ PROVISOIRE" % (pr, len(ok), 100.0*pr/len(ok)))
    print("     natif, banc repare, mesure et complet : 30,7 %%  n=127  IC95 [22,7 ; 38,7]")
    print("     (banc casse, tous deux retires : natif 59,6 %%  politique 44,2 %%)")
