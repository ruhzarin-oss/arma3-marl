#!/usr/bin/env python3
"""Le couvert change-t-il la donne ? Lecture du banc."""
import re, sys
from collections import defaultdict
LOG = sys.argv[1] if len(sys.argv)>1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
d = defaultdict(list); bl = defaultdict(list)
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|CV\|essai\|(\w+)\|(\w+)\|(\d+)\|(\d+)\|know\|([\d.]+)\|bloque\|(\d+)\|sur\|(\d+)', l)
    if m:
        d[(m.group(1), m.group(2), int(m.group(3)))].append(float(m.group(5)))
        bl[(m.group(1), m.group(2))].append(int(m.group(6)))
n = sum(len(v) for v in d.values())
print(f"  essais : {n} / 54")
if not n: sys.exit()
NOM = {'UP':'debout','MIDDLE':'accroupi','DOWN':'couché'}
CV  = {'aucun':'terrain nu','bas':'obstacle 1 m','haut':'mur 1,8 m'}
print(f"\n  {'couvert':>13s} {'posture':>9s} {'60 m':>7s} {'100 m':>7s} {'150 m':>7s}   (knowsAbout, 0 = jamais repéré)")
for c in ('aucun','bas','haut'):
    for p in ('UP','MIDDLE','DOWN'):
        cs = []
        for dist in (60,100,150):
            v = d.get((c,p,dist), [])
            cs.append(f"{sum(v)/len(v):.2f}" if v else "  —  ")
        if any(x != "  —  " for x in cs):
            print(f"  {CV[c]:>13s} {NOM[p]:>9s} {cs[0]:>7s} {cs[1]:>7s} {cs[2]:>7s}")
print(f"\n  LE COUVERT MASQUE-T-IL ? (défenseurs dont la vue est coupée, sur 6)")
for c in ('bas','haut'):
    for p in ('UP','MIDDLE','DOWN'):
        v = bl.get((c,p), [])
        if v: print(f"    {CV[c]:>13s} {NOM[p]:>9s}  {sum(v)/len(v):.1f} / 6")
print(f"\n  MOYENNE PAR CONDITION")
pc = defaultdict(list)
for (c,p,dist), v in d.items(): pc[(c,p)] += v
for c in ('aucun','bas','haut'):
    li = []
    for p in ('UP','MIDDLE','DOWN'):
        v = pc.get((c,p), [])
        li.append(f"{NOM[p]} {sum(v)/len(v):.2f}" if v else f"{NOM[p]} —")
    print(f"    {CV[c]:>13s} : " + "   ".join(li))
# la question
for c in ('bas','haut'):
    up = pc.get((c,'UP'), []); dw = pc.get((c,'DOWN'), [])
    if up and dw:
        u = sum(up)/len(up); w = sum(dw)/len(dw)
        print(f"\n  DERRIÈRE {CV[c].upper()} : debout {u:.2f}  ->  couché {w:.2f}"
              f"   {'-> SE COUCHER PAIE' if w < u*0.6 else '-> pas d effet net'}")
