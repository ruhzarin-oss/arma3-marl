#!/usr/bin/env python3
"""arr_plancher.py — « LE FLANC FAIT ARRIVER » : synergie, ou deux billets de loterie ?

⟨Fable, 05/08 : « fais le calcul AVANT d'ecrire la phrase — il est gratuit et il decide
 entre DEUX resultats differents. »⟩

LE PIEGE. Le deux-axes a DEUX chances d'arriver, le frontal une seule. « 83 axes arrives sur
84 engagements contre 26 sur 64 » est donc spectaculaire mais en partie MECANIQUE.

LE TEST. On compare le « au moins un axe arrive » OBSERVE au PLANCHER de deux tentatives
INDEPENDANTES : 1 - (1-p)^2, ou p est le taux d'arrivee par axe mesure sur le frontal.

  au-dessus du plancher  -> les axes se COUVRENT : l'un fixe, l'autre passe. C'est le
                            mecanisme cherche depuis le debut.
  AU plancher            -> « deux axes = deux billets de loterie ». Redondance pure, pas
                            synergie. La phrase se retrograde en « deux chances ».
  en dessous             -> ils se GENENT.

CONDITION D'ECHEC, deposee par Fable avant ce calcul : si l'observe ne depasse pas
1-(1-p)^2, la phrase « le flanc fait arriver » devient « deux axes = deux chances », et
c'est CETTE phrase-la qu'on verse au projet.
"""
import re, sys, math
from collections import defaultdict

# CORPUS N1, CLOS. Le journal vif (serverBA.out) est une REPLICATION INDEPENDANTE :
# il se juge a part, a la regle d arret de CRITERES_REPLICATION_AB.md. Ne pas cumuler.
JOURNAUX = ['/mnt/data/harmattan-sandbox/logs/serverBA_ab_reel_partie1.out',
            '/mnt/data/harmattan-sandbox/logs/serverBA_ab_reel_partie2.out']

D, ARR = {}, defaultdict(set)
FIN = set()
for i, ch in enumerate(JOURNAUX):
    dec = i*100000
    try: f = open(ch, errors='ignore')
    except FileNotFoundError: continue
    for l in f:
        m = re.search(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|\d+\|\d+\|\d+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)', l)
        if m: D[int(m.group(1))+dec] = (int(m.group(2)), int(m.group(3)))   # axes, fige
        m = re.search(r'HMT\|G\|ARR\|(\d+)\|[\d.]+\|(\d+)\|', l)
        if m: ARR[int(m.group(1))+dec].add(int(m.group(2)))                 # axes DISTINCTS
        m = re.search(r'HMT\|G\|fin\|(\d+)\|', l)
        if m: FIN.add(int(m.group(1))+dec)

clos = [k for k in D if k in FIN]
fr = [k for k in clos if D[k][0] == 1 and D[k][1] == 0]
dx = [k for k in clos if D[k][0] == 2 and D[k][1] == 0]

# frontal : un seul axe, donc « au moins un » == « l'axe arrive »
n_fr = len(fr); a_fr = sum(1 for k in fr if len(ARR.get(k, ())) >= 1)
p_axe_fr = a_fr / max(n_fr, 1)

# deux axes : on compte les axes DISTINCTS ayant franchi
n_dx = len(dx)
axes_dx = sum(len(ARR.get(k, ())) for k in dx)
p_axe_dx = axes_dx / max(2*n_dx, 1)
au_moins_un = sum(1 for k in dx if len(ARR.get(k, ())) >= 1)
les_deux = sum(1 for k in dx if len(ARR.get(k, ())) >= 2)
obs = au_moins_un / max(n_dx, 1)

plancher = 1 - (1 - p_axe_fr)**2

print("\n" + "="*74)
print("  TAUX D'ARRIVEE PAR AXE   (un axe « arrive » = il franchit le rayon de tenue)")
print("  " + "-"*72)
print(f"     frontal    {a_fr:3d} axes arrives / {n_fr:3d} axes engages   ->  p = {p_axe_fr:.3f}")
print(f"     deux_axes  {axes_dx:3d} axes arrives / {2*n_dx:3d} axes engages   ->  p = {p_axe_dx:.3f}")
print("="*74)
print("\n  « AU MOINS UN AXE ARRIVE », par engagement a deux axes")
print("  " + "-"*72)
print(f"     OBSERVE                             {au_moins_un:3d}/{n_dx:3d}  =  {obs:.1%}")
print(f"     PLANCHER de deux tentatives         1-(1-{p_axe_fr:.3f})^2  =  {plancher:.1%}")
print(f"     ecart au plancher                   {obs-plancher:+.1%}")
print(f"     ⟨les DEUX axes arrivent : {les_deux}/{n_dx} = {les_deux/max(n_dx,1):.1%}⟩")

# significativite de l'ecart au plancher, test binomial normal
if n_dx > 0 and 0 < plancher < 1:
    s = math.sqrt(plancher*(1-plancher)/n_dx)
    z = (obs - plancher)/s if s > 0 else 0
    pv = math.erfc(abs(z)/math.sqrt(2))
    print(f"     z = {z:+.2f} · p = {pv:.4f}")

print("\n" + "="*74)
if obs > plancher and pv < 0.05:
    print("  LES AXES SE COUVRENT. Le « au moins un arrive » DEPASSE ce que donneraient deux")
    print("  tentatives independantes : ce n'est pas un effet de nombre, c'est une SYNERGIE.")
    print("  -> « le flanc fait ARRIVER » se verse au projet.")
elif obs > plancher:
    print("  AU-DESSUS DU PLANCHER, MAIS PAS SIGNIFICATIVEMENT. Le sens est bon, la force")
    print("  manque. On verse « deux axes = deux chances », et la synergie reste a etablir.")
else:
    print("  AU PLANCHER OU EN DESSOUS. « Deux axes = deux billets de loterie » : redondance")
    print("  pure, pas synergie. C'est CETTE phrase-la qu'on verse au projet, pas l'autre.")
print("  " + "="*72)
print(f"\n  ⟨et le taux PAR AXE : {p_axe_dx:.3f} contre {p_axe_fr:.3f} — un axe engage a deux")
print(f"   reussit-il mieux qu'un axe engage seul ? C'est la meme question, vue de l'autre bout.⟩")
