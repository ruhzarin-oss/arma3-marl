#!/usr/bin/env python3
"""Où le cône se ferme-t-il exactement ?"""
import re, sys
from collections import defaultdict
LOG = sys.argv[1] if len(sys.argv)>1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
d = defaultdict(list)
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|CN\|essai\|(\d+)\|(\d+)\|(\d+)\|know\|([\d.]+)', l)
    if m: d[int(m.group(1))].append(float(m.group(4)))
n = sum(len(v) for v in d.values())
print(f"  essais : {n} / 24")
if not n: sys.exit()
print()
print("   azimut    n   moyenne   valeurs")
for az in sorted(d):
    v = d[az]
    barre = "#" * int(round(sum(v)/len(v) * 8))
    print(f"   {az:>4d}deg  {len(v):>3d}   {sum(v)/len(v):>6.2f}   {barre:<32s} {v}")
azs = sorted(d)
dedans = [a for a in azs if sum(d[a])/len(d[a]) > 2.0]
dehors = [a for a in azs if sum(d[a])/len(d[a]) < 0.5]
if dedans and dehors:
    print()
    print(f"  detecte jusqu a {max(dedans)}deg  ·  aveugle des {min(dehors)}deg")
    print(f"  -> la bascule est entre {max(dedans)} et {min(dehors)} degres")
    interieur = [sum(d[a])/len(d[a]) for a in dedans]
    plat = max(interieur) - min(interieur) < 0.5
    print(f"  -> a l interieur du cone : {'PLATEAU PLAT a ' + f'{sum(interieur)/len(interieur):.2f}' if plat else 'DECROISSANCE progressive'}")
