#!/usr/bin/env python3
"""Vitesse réelle selon posture et allure."""
import re, sys
from collections import defaultdict
LOG = sys.argv[1] if len(sys.argv)>1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
d = defaultdict(list); ecart = 0
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|VT\|essai\|(\w+)\|(\w+)\|(\d+)\|arrive\|(\d)\|duree\|([\d.]+)\|parcouru\|(\d+)\|vitesse\|([\d.]+)\|posture_tenue\|([\d.]+)', l)
    if m:
        if m.group(4) == '0' or float(m.group(8)) < 0.8: ecart += 1; continue
        d[(m.group(1), m.group(2))].append(float(m.group(7)))
n = sum(len(v) for v in d.values())
print(f"  essais retenus : {n} / 27   ecartes (non arrives ou posture non tenue) : {ecart}")
if not n: sys.exit()
NOM = {'UP':'debout', 'MIDDLE':'accroupi', 'DOWN':'couche'}
AL  = {'LIMITED':'lent', 'NORMAL':'normal', 'FULL':'course'}
print()
print(f"   {'posture':>10s} {'lent':>8s} {'normal':>8s} {'course':>8s}   (m/s)")
ref = None
for po in ('UP','MIDDLE','DOWN'):
    li = []
    for al in ('LIMITED','NORMAL','FULL'):
        v = d.get((po,al), [])
        li.append(f"{sum(v)/len(v):8.2f}" if v else "     —  ")
    print(f"   {NOM[po]:>10s} " + " ".join(li))
    if po == 'UP':
        v = d.get(('UP','FULL'), [])
        if v: ref = sum(v)/len(v)
if ref:
    print(f"\n   RAPPORT A LA COURSE DEBOUT ({ref:.2f} m/s)")
    for po in ('UP','MIDDLE','DOWN'):
        v = d.get((po,'FULL'), [])
        if v:
            r = (sum(v)/len(v))/ref
            print(f"     {NOM[po]:>10s} : {r:.2f}"
                  + ("      <- j'avais code 1,00" if po=='UP' else
                     "      <- j'avais code 0,60" if po=='MIDDLE' else
                     "      <- j'avais code 0,33"))
