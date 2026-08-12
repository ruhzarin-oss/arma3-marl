#!/usr/bin/env python3
"""aiguille_bond.py — L AIGUILLE, ET RIEN D AUTRE.

Deux nombres : le taux d ARRIVEE de chaque bras. Les reactions permises sont deposees dans
PROTOCOLE_AIGUILLE_BOND.md, ECRIT AVANT cette lecture. Ce script ne calcule NI l ecart entre
les bras, NI sa significativite, NI le classement des couloirs — il repond a une seule
question : l instrument peut-il bouger ?
"""
import re
F = '/mnt/data/harmattan-sandbox/logs/serverBA.out'
lieu = re.compile(r'HMT\|G\|LIEU\|(\d+)\|(\d+)\|(\d+)')
arr  = re.compile(r'HMT\|G\|ARR\|(\d+)\|')
bras, arrives = {}, set()
for L in open(F, encoding='utf-8', errors='ignore'):
    m = lieu.search(L)
    if m:
        bras[int(m.group(1))] = (int(m.group(3)), int(m.group(2)))
    m = arr.search(L)
    if m:
        arrives.add(int(m.group(1)))
# on ne juge que les accrochages TERMINES : le dernier ouvert n a pas eu sa chance
if bras:
    dernier = max(bras)
    clos = {k: v for k, v in bras.items() if k < dernier}
else:
    clos = {}
for b, nom in ((1, 'professeur (bond)'), (0, 'temoin (simultane)')):
    ids = [k for k, v in clos.items() if v[0] == b]
    n = len(ids)
    a = sum(1 for k in ids if k in arrives)
    p = 100.0 * a / n if n else -1
    etat = 'BANDE' if 20 <= p <= 80 else 'BUTOIR'
    print(f"  {nom:<22} {a:3d} arrivees sur {n:3d}  =  {p:5.1f} %   {etat}")
print(f"\n  accrochages clos : {len(clos)} · couloirs vus : {len(set(v[1] for v in clos.values()))}")
