#!/usr/bin/env python3
"""LECTURE PROVISOIRE de la passe 1 du natif reparee. ⚠️ CE N EST PAS UN VERDICT.
Le predicat depose exige DEUX passes et une concordance a moins de 10 points ; une passe
seule ne se cite pas. On la lit avec le lecteur DEPOSE, sans y toucher.
"""
import glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN
import re
E = [e for e in (LN.lire(f) for f in sorted(glob.glob("/mnt/data/natif2/p1_e*.txt"))) if e]
ok = [e for e in E if e["etat"] == "ok"]
mp = sorted(e["mpas"] for e in ok)
print("\n  ══ NATIF REPARE, passe 1 — PROVISOIRE ══")
print("  episodes complets : %d   retenus : %d" % (len(E), len(ok)))
for k in sorted(set(e["etat"] for e in E)):
    print("    %-16s %d" % (k, sum(1 for e in E if e["etat"] == k)))
if mp:
    print("  condition 2 · le monde bouge : mediane %.2f m/pas -> %s"
          % (mp[len(mp)//2], "PASSE" if mp[len(mp)//2] > 1.0 else "⛔ NON"))
cps = sorted(e["coups"] for e in ok if e["coups"] >= 0)
if cps: print("  condition 3 · coups attaquants : mediane %d" % cps[len(cps)//2])
if ok:
    pr = sum(1 for e in ok if e["prise"])
    print("\n  ➤ PRISES : %d / %d = %.1f %%   ⚠️ PROVISOIRE, une passe ne se cite pas"
          % (pr, len(ok), 100.0*pr/len(ok)))
    print("     (pour memoire, meme bras sur le banc CASSE : passe 1 = 56,1 %)")
