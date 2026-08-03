#!/usr/bin/env python3
"""Combien de temps le camp se souvient-il ?"""
import re, sys
from collections import defaultdict
LOG = sys.argv[1] if len(sys.argv)>1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
acq = defaultdict(list); suivi = defaultdict(lambda: defaultdict(list)); ecarte = []
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|MM\|acquis\|(\w+)\|(\d+)\|([\d.]+)', l)
    if m: acq[m.group(1)].append(float(m.group(3)))
    m = re.search(r'HMT\|MM\|suivi\|(\w+)\|(\d+)\|(\d+)\|([\d.]+)', l)
    if m: suivi[m.group(1)][int(m.group(3))].append(float(m.group(4)))
    m = re.search(r'HMT\|MM\|ECARTE\|(\w+)\|(\d+)', l)
    if m: ecarte.append((m.group(1), m.group(2)))
NOM = {'efface':'retiré de la vue', 'reste':'reste visible', 'jamais':'jamais vu'}
print("  ACQUISITION (avant retrait)")
for c in ('efface','reste','jamais'):
    v = acq.get(c, [])
    if v: print(f"    {NOM[c]:>18s}  n={len(v)}  connaissance {sum(v)/len(v):.2f}")
if ecarte: print(f"    essais écartés (acquisition < 3,0) : {len(ecarte)}")
if not suivi: print("\n  pas encore de suivi"); sys.exit()
pts = sorted({t for c in suivi for t in suivi[c]})
aff = [t for t in pts if t % 30 == 0][:11]
print(f"\n  DÉCROISSANCE  (connaissance du camp, 0 = oubli total)")
print(f"    {'condition':>18s} " + " ".join(f"{t:>5d}s" for t in aff))
for c in ('efface','reste','jamais'):
    if c not in suivi: continue
    li = []
    for t in aff:
        v = suivi[c].get(t, [])
        li.append(f"{sum(v)/len(v):5.2f}" if v else "  —  ")
    print(f"    {NOM[c]:>18s} " + " ".join(li))
print()
ef = suivi.get('efface', {}); rs = suivi.get('reste', {})
comm = sorted(set(ef) & set(rs))     # on ne compare que sur les instants COMMUNS aux deux
if ef and rs and len(comm) >= 2:
    t0, tf = comm[0], comm[-1]
    a = sum(ef[t0])/len(ef[t0]); b = sum(ef[tf])/len(ef[tf])
    ra = sum(rs[t0])/len(rs[t0]); rb = sum(rs[tf])/len(rs[tf])
    print(f"  retiré de la vue : {a:.2f} a {t0}s  ->  {b:.2f} a {tf}s   ({(b-a)/max(a,1e-9):+.0%})")
    print(f"  reste visible    : {ra:.2f} a {t0}s  ->  {rb:.2f} a {tf}s   ({(rb-ra)/max(ra,1e-9):+.0%})   <- CONTROLE")
    print()
    if abs((rb-ra)/max(ra,1e-9)) > 0.2:
        print("  -> le CONTROLE decroit aussi : ce n est pas la perte de vue qu on mesure.")
    elif (a-b)/max(a,1e-9) < 0.15:
        print("  -> LA MEMOIRE NE S EFFACE PAS. Se faire voir une fois est definitif.")
    else:
        seuil = a/2; dv = None
        for t in sorted(ef):
            if sum(ef[t])/len(ef[t]) <= seuil: dv = t; break
        print(f"  -> LA MEMOIRE S EFFACE." + (f" Demi-vie ~{dv} s." if dv else " Plus lentement que la fenetre."))
elif ef:
    t0, tf = min(ef), max(ef)
    a = sum(ef[t0])/len(ef[t0]); b = sum(ef[tf])/len(ef[tf])
    print(f"  retire de la vue : {a:.2f} a {t0}s -> {b:.2f} a {tf}s   ({(b-a)/max(a,1e-9):+.0%})")
    print("  (controle « reste visible » pas encore complet — on ne conclut pas)")
