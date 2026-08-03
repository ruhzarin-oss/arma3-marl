#!/usr/bin/env python3
"""Tirer révèle-t-il ? Lecture du banc."""
import re, sys
from collections import defaultdict
LOG = sys.argv[1] if len(sys.argv)>1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
d = defaultdict(list); cp = defaultdict(list)
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|TR\|essai\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|avant\|([\d.]+)\|apres\|([\d.]+)\|coups_reels\|(\d+)', l)
    if m:
        k = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        d[k].append((float(m.group(5)), float(m.group(6))))
        cp[k].append(int(m.group(7)))
n = sum(len(v) for v in d.values())
print(f"  essais : {n} / 32")
if not n: sys.exit()
print(f"\n  {'position':>9s} {'dist':>6s} {'coups':>6s} {'reels':>6s} {'avant':>7s} {'apres':>7s}")
for k in sorted(d):
    v = d[k]
    a = sum(x[0] for x in v)/len(v); b = sum(x[1] for x in v)/len(v)
    cr = sum(cp[k])/len(cp[k])
    lib = "dans cone" if k[0] == 0 else "dans dos"
    print(f"  {lib:>9s} {k[1]:>5d}m {k[2]:>6d} {cr:>6.1f} {a:>7.2f} {b:>7.2f}")
print("\n  TIRER DEPUIS L'ANGLE MORT REVELE-T-IL ?")
for dist in (100, 200):
    base = d.get((180, dist, 0), [])
    if not base: continue
    b0 = sum(x[1] for x in base)/len(base)
    print(f"\n    a {dist} m, dans le dos :")
    print(f"      sans tirer ........ {b0:.2f}   (contrôle nul : doit être ~0)")
    for c in (1, 5, 15):
        v = d.get((180, dist, c), [])
        if v:
            b = sum(x[1] for x in v)/len(v)
            r = sum(cp[(180,dist,c)])/len(cp[(180,dist,c)])
            etat = "REVELE" if b > 0.5 else "toujours invisible"
            print(f"      apres {c:2d} coups ({r:.0f} reels) : {b:.2f}   -> {etat}")
