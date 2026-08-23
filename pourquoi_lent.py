#!/usr/bin/env python3
"""POURQUOI LE NATIF AVANCE-T-IL SI PEU SUR LE BANC REPARE ?

Trois explications possibles, et elles ne se ressemblent pas :
  A. il se BAT — il progresse par bonds, se couche sous le feu, et c est du combat reel
  B. il MEURT tot — la distance cesse de bouger parce qu il n y a plus personne
  C. il n a jamais recu son ordre — la reparation du pas 0 ne marche pas

On les separe : profil moyen de la distance ET des vivants, pas par pas, et la part des
episodes ou l escouade est morte avant le pas 30.
"""
import re, glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN
RE_L = re.compile(r'^\s+(\d+)\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', re.M)

def trace(f):
    t = open(f, errors="ignore").read()
    return [(int(p), int(v), int(d)) for p, v, _, d in RE_L.findall(t)]

def profil(dos, etiq):
    par = {}; morts30 = 0; n = 0; ordre = 0
    for f in sorted(glob.glob("%s/p1_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok": continue
        n += 1
        if "HARMATTAN_ORDRE_NATIF" in open(f, errors="ignore").read(): ordre += 1
        lg = trace(f)
        for p, v, d in lg:
            par.setdefault(p, []).append((v, d))
        vv = [v for p, v, d in lg if p <= 30]
        if vv and vv[-1] == 0: morts30 += 1
    print("\n  ══ %s ══  n=%d" % (etiq, n))
    print("  %5s %10s %12s %10s" % ("pas", "vivants", "distance", "episodes"))
    for p in sorted(par):
        if p % 10 and p not in (5, 59): continue
        v = par[p]
        dd = [d for _, d in v if d >= 0]
        print("  %5d %10.2f %11.0f m %10d" % (p, sum(x for x, _ in v)/len(v),
                                              (sum(dd)/len(dd)) if dd else -1, len(v)))
    print("  escouade morte avant le pas 30 : %d sur %d" % (morts30, n))
    if etiq.startswith("NATIF REPARE"):
        print("  ordre du pas 0 present dans le journal : %d sur %d" % (ordre, n))

profil("/mnt/data/natif2", "NATIF REPARE")
profil("/mnt/data/natif", "NATIF, banc casse (pour comparer)")
