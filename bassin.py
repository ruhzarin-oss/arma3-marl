#!/usr/bin/env python3
"""bassin — CARACTERISER LE BASSIN, PUIS LE DECOUPER.

⚠️ Le site gele du barreau certifie est [8126.45, 10395.4] az=310. Il n'est PAS sur la
grille de prospection (pas de 80 m depuis [8291.45, 10065.42]) ni sur ses azimuts (pas
de 30°). Il est donc exclu par construction — mais on le VERIFIE au lieu de le supposer.
"""
import re, statistics as st

GELE = (8126.45, 10395.4, 310)
lignes = []
for l in open("/home/younes/arma3-marl/bassin_fin.txt"):
    m = re.search(r"BASSIN ([\d.-]+) ([\d.-]+) (\d+) ([\d.-]+) ([\d.-]+) ([\d.-]+)", l)
    if m:
        x, y, az, cl, dev, pente = float(m[1]), float(m[2]), int(m[3]), float(m[4]), float(m[5]), float(m[6])
        lignes.append(dict(x=x, y=y, az=az, cl=cl, dev=dev, pente=pente, score=cl - 0.4*dev))

print(f"{len(lignes)} candidats\n")
def q(v, p): 
    v = sorted(v); k = (len(v)-1)*p; i = int(k)
    return v[i] if i+1 >= len(v) else v[i] + (k-i)*(v[i+1]-v[i])

for nom, cle in [("degagement", "cl"), ("rugosite", "dev"), ("score", "score"), ("pente", "pente")]:
    v = [r[cle] for r in lignes]
    print(f"  {nom:11s} min={min(v):7.3f}  q25={q(v,.25):7.3f}  med={q(v,.5):7.3f}  "
          f"q75={q(v,.75):7.3f}  max={max(v):7.3f}")

print(f"\n  pour memoire, le site GELE du barreau certifie : score 1.32")
sur = [r for r in lignes if abs(r['x']-GELE[0]) < 1 and abs(r['y']-GELE[1]) < 1]
print(f"  le site gele est-il dans le bassin ? {'OUI — PROBLEME' if sur else 'non, exclu par construction'}")

print(f"\n  candidats de score >= 1.32 (au moins aussi bons que le gele) : "
      f"{sum(1 for r in lignes if r['score'] >= 1.32)}")
for s in [0.0, 0.5, 1.0, 1.32, 2.0]:
    print(f"    score >= {s:4.2f} : {sum(1 for r in lignes if r['score'] >= s):4d}")
print(f"\n  pentes : |p| <= 5 %% : {sum(1 for r in lignes if abs(r['pente'])<=0.05):4d}   "
      f"|p| <= 10 %% : {sum(1 for r in lignes if abs(r['pente'])<=0.10):4d}   "
      f"|p| > 20 %% : {sum(1 for r in lignes if abs(r['pente'])>0.20):4d}")
