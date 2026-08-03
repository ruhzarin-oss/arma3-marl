#!/usr/bin/env python3
"""Le chemin de l'agent transfere-t-il ? Metrique : DISTANCE de detection.

⟨le controle positif du 03/08 a invalide la metrique precedente : le chemin OPTIMAL etait
 detecte 7/7 comme la ligne droite, ecart 0 %. On ne peut pas atteindre le centre d une
 position sans etre vu. Ce que le contournement achete, c est d etre vu PLUS LOIN.⟩
"""
import re, sys
from collections import defaultdict
LOG = sys.argv[1] if len(sys.argv)>1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
k = defaultdict(dict); dd = defaultdict(dict); rs = defaultdict(dict)
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|AG\|essai\|(\d+)\|(\w+)\|know\|([\d.]+)\|reste\|(\d+)\|dist_detect\|(-?\d+)', l)
    if m:
        c, lib = int(m.group(1)), m.group(2)
        k[c][lib] = float(m.group(3)); rs[c][lib] = int(m.group(4)); dd[c][lib] = int(m.group(5))
comp = [c for c in k if 'agent' in k[c] and 'droite' in k[c]]
print(f"  configurations completes : {len(comp)} / 20")
if not comp:
    print(f"  ({sum(len(v) for v in k.values())} trajectoires rejouees)"); sys.exit()

vues = [c for c in comp if k[c]['droite'] >= 1.5]
print(f"\n  CONTROLE — lignes droites detectees : {len(vues)} / {len(comp)}")
if not vues: print("  aucune config exploitable"); sys.exit()
arr = [c for c in vues if rs[c]['agent'] <= 45]
print(f"  CONTROLE — l agent finit a moins de 45 m : {len(arr)} / {len(vues)}")
if not arr: print("  l agent n arrive jamais"); sys.exit()

# distance de detection : -1 = jamais detecte, on le compte comme la distance de depart
def dist(c, lib):
    v = dd[c][lib]
    return 80 if v < 0 else v
da = sum(dist(c,'agent') for c in arr)/len(arr)
dg = sum(dist(c,'droite') for c in arr)/len(arr)
ja = sum(1 for c in arr if dd[c]['agent'] < 0)
jg = sum(1 for c in arr if dd[c]['droite'] < 0)
print(f"\n  sur {len(arr)} configurations valides")
print(f"    ligne droite : repere a {dg:5.1f} m de l objectif   (jamais repere : {jg}/{len(arr)})")
print(f"    AGENT        : repere a {da:5.1f} m de l objectif   (jamais repere : {ja}/{len(arr)})")
ecart = (da-dg)/max(dg,1e-9)
print(f"\n    l agent est repere {ecart:+.0%} plus LOIN   (seuil ecrit avant : +25 %)")
print()
if ecart >= 0.25:
    print("  LE CHEMIN TRANSFERE. Le contournement appris dans la sandbox achete")
    print("  de la distance dans Arma — c est exactement ce qu il doit acheter.")
else:
    print("  LE CHEMIN NE TRANSFERE PAS, sur cette metrique corrigee.")
    print("  Verifier d abord le controle positif : le chemin OPTIMAL doit, lui, passer.")
