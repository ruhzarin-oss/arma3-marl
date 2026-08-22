#!/usr/bin/env python3
"""COMBIEN DE PAS POUR ARRIVER ? — la seule grandeur comparable entre les deux mondes.

Les metres ne se comparent pas (le gymnase a son echelle), les secondes non plus. Mais le
BUDGET est le meme des deux cotes : 60 pas, et la meme distance de depart en proportion du
terrain. Donc : au bout de combien de PAS l escouade passe-t-elle sous 25 m ?

Si le gymnase arrive au pas 12 et Arma au pas 35, une politique reglee sur le premier
n a aucune raison de savoir se rationner dans le second.
"""
import re, glob, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN
import boucle as B
from porter_boucle import charger

RE_L = re.compile(r'^\s+(\d+)\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', re.M)

def arrivee(f):
    t = open(f, errors="ignore").read()
    lg = [(int(p), int(v), int(d)) for p, v, _, d in RE_L.findall(t)]
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(-?\d+)', t)
    if fin: lg.append((int(fin.group(1)), int(fin.group(2)), int(fin.group(3))))
    for p, v, d in lg:
        if v > 0 and 0 <= d < 25: return p, lg[0][2]
    return None, (lg[0][2] if lg else -1)

print("\n  ══ ARMA ══")
for nom, dos in [("NATIF", "/mnt/data/natif"), ("POLITIQUE", "/mnt/data/politique")]:
    pas = []; d0 = []
    for f in sorted(glob.glob("%s/p*_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok": continue
        p, dd = arrivee(f)
        if dd >= 0: d0.append(dd)
        if p is not None: pas.append(p)
    pas.sort()
    print("  %-11s arrivees : %3d   pas mediane : %2d   90e cent. : %2d   depart median : %d m"
          % (nom, len(pas), pas[len(pas)//2], pas[int(0.9*len(pas))], sorted(d0)[len(d0)//2]))

print("\n  ══ GYMNASE, meme politique, memes graines de test ══")
pol = charger("cpu"); DEV = next(pol.parameters()).device
prem = []
for g in B.GRAINES_TEST[:3]:
    e = B.monde(256, g); o = e.reset()
    d0 = torch.sqrt(e.apx**2 + e.apy**2).mean(1)
    vu = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(60):
        with torch.no_grad():
            a = pol(o.to(DEV))[0].argmax(-1).to(o.device)
        o, _, done, info = e.step(a, auto_reset=False)
        n = info["took"] & ~vu
        if bool(n.any()): prem += [t]*int(n.sum()); vu |= n
        if bool(done.all()): break
    if g == B.GRAINES_TEST[0]:
        print("  depart median : %.0f m (echelle du gymnase, terrain 200)" % float(d0.median()))
prem.sort()
print("  GYMNASE     arrivees : %3d   pas mediane : %2d   90e cent. : %2d"
      % (len(prem), prem[len(prem)//2], prem[int(0.9*len(prem))]))
