#!/usr/bin/env python3
"""terme_temoin.py — RECONSTITUER LE CORPUS TEL QU IL ETAIT QUAND LA REGLE A FIRE.

Regle deposee dans CRITERES_TEMOIN_VISE.md : « jugement UNIQUE, au premier de ces termes :
>= 120 accrochages clos par bras, ou 08h00 le 7 aout ».

Le serveur a continue apres. On ne juge pas sur 1040 accrochages parce qu ils sont la : on
reconstitue le corpus au moment ou la regle a fire, ce que les identifiants et les horodatages
permettent — sur pieces.
"""
import re, sys

J = '/mnt/data/harmattan-sandbox/logs/serverBA.out'
R_DEB = re.compile(r'^\s*(\d+):(\d+):\d+ .*HMT\|G\|debut\|(\d+)\|.*?\|(\d)\|(\d)"?\s*$')
R_FIN = re.compile(r'^\s*(\d+):(\d+):\d+ .*HMT\|G\|fin\|(\d+)\|')

axes, ordre = {}, []
JOUR, PREC = 0, 0
for l in open(J, errors='ignore'):
    m = R_DEB.search(l)
    if m:
        axes[int(m.group(3))] = int(m.group(4))
        continue
    m = R_FIN.search(l)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        mn = h * 60 + mi
        # le run a demarre a 17h09 le 06/08 et a franchi MINUIT : sans compteur de jour,
        # « 17h11 » passe pour « apres 08h00 » et la regle fire au premier accrochage.
        global JOUR, PREC
        if mn < PREC - 60:
            JOUR += 1
        PREC = mn
        ordre.append((JOUR * 1440 + mn, int(m.group(3))))

print(f"\n  {len(ordre)} accrochages clos au total · {len(axes)} debuts lus")
n1 = n2 = 0
terme = None
for rang, (mn, i) in enumerate(ordre, 1):
    a = axes.get(i)
    if a == 1:
        n1 += 1
    elif a == 2:
        n2 += 1
    if terme is None and (min(n1, n2) >= 120 or mn >= 1440 + 8 * 60):
        terme = (rang, mn, i, n1, n2)
if terme:
    rang, mn, i, n1, n2 = terme
    cause = "120 par bras" if min(n1, n2) >= 120 else "08h00"
    print(f"  LA REGLE A FIRE au {rang}e accrochage clos, a {(mn%1440)//60:02d}h{mn%60:02d} (jour +{mn//1440})"
          f"  (accrochage n°{i})")
    print(f"  cause : {cause}   ·   frontal {n1} · deux_axes {n2}")
    print(f"\n  -> le corpus a juger s arrete a l accrochage n°{i}."
          f" Les {len(ordre)-rang} suivants ne se lisent PAS.")
else:
    print("  la regle n a pas encore fire sur ce journal")
