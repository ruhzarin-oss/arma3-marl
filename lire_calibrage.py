#!/usr/bin/env python3
"""lire_calibrage.py — LE TAUX DE RESOLUTION, ET RIEN D'AUTRE.

⟨Fable, 05/08 : « calibre EN AVEUGLE — pendant le reglage tu ne lis QUE le taux de
 resolution, jamais les scores frontal/deux_axes. »⟩

Ce depouilleur ne PEUT pas montrer autre chose : le generateur tourne en mode calibrage,
qui ne produit QU'UN SEUL BRAS. L'aveuglement est structurel, pas disciplinaire.

LA CIBLE N'EST PAS LA MIENNE. Elle est deposee dans l'en-tete du generateur, avec sa raison
ecrite, bien avant cette nuit :

    « CIBLE DE PILOTAGE : 40 a 60 % d accrochages resolus. Tout se resout -> le monde
      recompense la charge. Rien ne se resout -> il n enseigne rien sur la prise.
      La frontiere EST le signal. »

On cherche donc la tranche de rapport de force qui ramene le taux dans cette fenetre.
Le ratio se relit dans `debut` : nAtt / nDef. Un seul passage balaye toute la plage.
"""
import re, sys
from collections import defaultdict

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'

deb, fin = {}, {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|', l)
    if m:
        deb[int(m.group(1))] = dict(campDef=int(m.group(2)), nDef=int(m.group(3)),
                                    nAtt=int(m.group(4)), dist=int(m.group(5)))
    m = re.search(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|(\d+)\|(\w+)\|\d+\|\d+\|(\d+)\|', l)
    if m:
        fin[int(m.group(1))] = dict(duree=int(m.group(2)), cause=m.group(3), pris=int(m.group(4)))

clos = sorted(set(deb) & set(fin))
print(f"\n  {len(deb)} accrochages ouverts · {len(clos)} clos")
if len(clos) < 8:
    print("  trop peu pour lire quoi que ce soit — laisser tourner.")
    sys.exit(0)

glob = sum(fin[k]['pris'] for k in clos) / len(clos)
print(f"  TAUX DE RESOLUTION GLOBAL : {glob:.1%}   (cible deposee : 40 a 60 %)")

TRANCHES = [(0.7, 1.1), (1.1, 1.5), (1.5, 1.9), (1.9, 2.4), (2.4, 3.1)]
print("\n" + "="*66)
print("  taux de prise PAR RAPPORT DE FORCE   (assaillants / defenseurs)")
print("  " + "-"*64)
print(f"  {'ratio':>12s} {'n':>5s} {'pris':>6s} {'taux':>8s}   {'dans la fenetre ?':>18s}")
bons = []
for lo, hi in TRANCHES:
    ks = [k for k in clos if lo <= deb[k]['nAtt']/max(deb[k]['nDef'], 1) < hi]
    if len(ks) < 4:
        print(f"  {lo:5.1f}-{hi:4.1f} {len(ks):5d}      .        .   (trop peu)")
        continue
    p = sum(fin[k]['pris'] for k in ks)
    t = p/len(ks)
    dedans = 0.40 <= t <= 0.60
    if dedans: bons.append((lo, hi, t, len(ks)))
    print(f"  {lo:5.1f}-{hi:4.1f} {len(ks):5d} {p:6d} {t:8.1%}   {'OUI' if dedans else 'non':>18s}")
print("="*66)

causes = defaultdict(int)
for k in clos: causes[fin[k]['cause']] += 1
print("  causes de fin : " + " · ".join(f"{c} {n}" for c, n in sorted(causes.items())))
d = [fin[k]['duree'] for k in clos]
print(f"  duree mediane : {sorted(d)[len(d)//2]} s")

print()
if bons:
    print("  TRANCHES DANS LA FENETRE :")
    for lo, hi, t, n in bons:
        print(f"     ratio {lo:.1f}-{hi:.1f}  ->  {t:.1%}  (n={n})")
    print("  -> reglage retenu : la tranche la plus fournie parmi celles-ci.")
else:
    print("  AUCUNE TRANCHE DANS LA FENETRE 40-60 %.")
    print("  Si cela tient sur un echantillon suffisant, la condition d'echec deposee")
    print("  s'applique : le monde du 02/08 est irrecuperable, et le +12,3 est retrograde")
    print("  d'axiome a observation historique.")
