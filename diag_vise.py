#!/usr/bin/env python3
"""diag_vise.py — POURQUOI 28 % DES HOMMES TOUCHES N ONT JAMAIS ETE DESIGNES ?

Le controle de coherence du temoin exigeait qu un assaillant TOUCHE ait ete designe cible
dans la minute precedente, dans >= 80 % des cas. Mesure : 72,0 %. Le depouilleur s est arrete
et n a pas lu les bras — c est ce qu il devait faire.

On ne baisse pas le seuil. On cherche POURQUOI, sur pieces. Trois lectures possibles, et la
mesure les separe :
  a) le tireur change de cible entre deux releves de 2 s        -> designe par QUELQU UN, oui,
                                                                   mais pas par SON tireur
  b) il tire sans cible assignee (tir d opportunite, arrosage)  -> jamais designe du tout
  c) mon fenetrage d une minute est trop court                  -> designe, mais plus tot
"""
import re
from collections import defaultdict

J = '/mnt/data/harmattan-sandbox/logs/serverBA_vise.out'
AXE = defaultdict(dict)
IMP = defaultdict(list)
VIS = defaultdict(list)

for l in open(J, errors='ignore'):
    m = re.search(r'HMT\|G\|POS\|(\d+)\|[\d.]+\|(\d+)\|\d+\|\d+\|\d+\|(-?\d+)', l)
    if m:
        AXE[int(m.group(1))][int(m.group(2))] = int(m.group(3))
        continue
    m = re.search(r'HMT\|G\|IMP\|(\d+)\|([\d.]+)\|(\d+)\|(\d+)\|', l)
    if m:
        IMP[int(m.group(1))].append((float(m.group(2)), int(m.group(3)), int(m.group(4))))
        continue
    m = re.search(r'HMT\|G\|VISE\|(\d+)\|([\d.]+)\|(\d+)\|(-?\d+)', l)
    if m:
        VIS[int(m.group(1))].append((float(m.group(2)), int(m.group(3)), int(m.group(4))))

n = jamais = par_qq_60 = par_qq_tot = par_son_tireur = 0
for a, lst in IMP.items():
    v = VIS.get(a, [])
    for t, tir, vic in lst:
        if AXE[a].get(vic, -1) < 0:
            continue
        n += 1
        vus = [(tv, d, c) for tv, d, c in v if c == vic]
        if not vus:
            jamais += 1
            continue
        par_qq_tot += 1
        if any(t - 60 <= tv <= t for tv, d, c in vus):
            par_qq_60 += 1
        if any(d == tir and t - 60 <= tv <= t for tv, d, c in vus):
            par_son_tireur += 1

print(f"\n  impacts sur assaillants : {n}")
print("  " + "-" * 66)
print(f"     JAMAIS designe par personne        {jamais:5d}  {jamais/max(n,1):6.1%}")
print(f"     designe par quelqu un, un jour     {par_qq_tot:5d}  {par_qq_tot/max(n,1):6.1%}")
print(f"     designe par quelqu un dans la min  {par_qq_60:5d}  {par_qq_60/max(n,1):6.1%}"
      f"   <- le controle lisait CA (seuil 80 %)")
print(f"     designe par SON TIREUR dans la min {par_son_tireur:5d}  {par_son_tireur/max(n,1):6.1%}")
print("  " + "-" * 66)
if jamais / max(n, 1) > 0.2:
    print("  LECTURE (b) : une part reelle des impacts vient de tirs SANS CIBLE ASSIGNEE —")
    print("  arrosage, tir d opportunite. Le controle supposait que tout impact suit une")
    print("  designation. C est FAUX dans Arma, et c est une propriete du monde, pas un bug.")
elif par_qq_tot / max(n, 1) - par_qq_60 / max(n, 1) > 0.05:
    print("  LECTURE (c) : ils ONT ete designes, mais plus tot que ma fenetre d une minute.")
else:
    print("  LECTURE (a) : le tireur change de cible entre deux releves de 2 s.")
