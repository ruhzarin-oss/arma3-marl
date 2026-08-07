#!/usr/bin/env python3
"""terme2.py — a quel accrochage la regle d arret a-t-elle fire ?

Regle deposee : « jugement UNIQUE, au premier de ces termes : >= 120 accrochages clos par
bras, ou 08h00 le 7 aout ». Le serveur a continue jusqu a 1051. On ne juge pas sur ce qui
existe : on reconstitue le corpus au moment ou la regle a fire.

PIEGE DEJA RENCONTRE : le run a demarre a 17h09 le 06/08 et a franchi MINUIT. Comparer des
heures d horloge sans date fait passer « 17h11 » pour « apres 08h00 ». On compte les jours.
"""
import re

J = '/mnt/data/harmattan-sandbox/logs/serverBA.out'
R_DEB = re.compile(r'HMT\|G\|debut\|(\d+)\|.*?\|(\d)\|(\d)"?\s*$')
R_FIN = re.compile(r'^\s*(\d+):(\d+):\d+ .*HMT\|G\|fin\|(\d+)\|')

axes = {}
ordre = []
jour = 0
prec = 0
for l in open(J, errors='ignore'):
    m = R_DEB.search(l)
    if m:
        axes[int(m.group(1))] = int(m.group(2))
        continue
    m = R_FIN.search(l)
    if m:
        mn = int(m.group(1)) * 60 + int(m.group(2))
        if mn < prec - 60:
            jour += 1
        prec = mn
        ordre.append((jour * 1440 + mn, mn, int(m.group(3))))

print(f"\n  {len(ordre)} accrochages clos · {len(axes)} debuts lus")
n1 = n2 = 0
terme = None
for rang, (abs_mn, mn, i) in enumerate(ordre, 1):
    a = axes.get(i)
    if a == 1:
        n1 += 1
    elif a == 2:
        n2 += 1
    if terme is None and (min(n1, n2) >= 120 or abs_mn >= 1440 + 8 * 60):
        terme = (rang, mn, abs_mn, i, n1, n2)
if terme:
    rang, mn, abs_mn, i, n1, n2 = terme
    cause = "120 par bras" if min(n1, n2) >= 120 else "08h00"
    print(f"  LA REGLE A FIRE au {rang}e accrochage clos, a {mn//60:02d}h{mn%60:02d}"
          f" (jour +{abs_mn//1440}) — accrochage n°{i}")
    print(f"  cause : {cause}   ·   frontal {n1} · deux_axes {n2}")
    print(f"  -> les {len(ordre)-rang} accrochages suivants NE SE LISENT PAS.")
else:
    print("  la regle n a pas fire sur ce journal")
