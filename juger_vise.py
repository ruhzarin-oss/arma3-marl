#!/usr/bin/env python3
"""juger_vise.py — LE TEMOIN D INTENTION, juge une seule fois.

Criteres deposes AVANT lancement : CRITERES_TEMOIN_VISE.md (commit af75a5d). Recopies :

  A  DESIGNATION       part d assaillants designes au moins une fois, moyenne PAR ACCROCHAGE
  B  DUREE             part des releves a 2 s ou l assaillant est designe, sur ses releves vivant
  C  DESIGNES SANS TIR part des designations non suivies d un TIR du meme defenseur en 4 s
                       — la mesure DIRECTE du sursis

  ETABLI  le deux_axes est designe MOINS LONGTEMPS (B, p < 0,05, ecart >= 6 points) ET la
          part de designations sans tir (C) est PLUS ELEVEE pour lui
  MORT    designe autant ou plus longtemps, et pas davantage de designations sans tir
  MIXTE   A, B et C ne concordent pas -> on garde les chiffres, PAS D HISTOIRE

  SENSIBILITE ecrite avant : ~10 points sur A, ~6 sur B.
  CONTROLES : >= 95 % des accrochages portent un releve VISE ; un assaillant TOUCHE doit avoir
  ete designe dans la minute precedente dans >= 80 % des cas ; le journal SANTE reste plat.

CORPUS FIGE au terme de la regle : accrochage n°247, 21h07 le 06/08, cause « 120 par bras ».
Les 822 accrochages produits ensuite ne se lisent PAS.
"""
import re, sys, math
from collections import defaultdict

J = '/mnt/data/harmattan-sandbox/logs/serverBA_vise.out'

D, F, AXE = {}, {}, defaultdict(dict)
VISE = defaultdict(lambda: defaultdict(int))     # acc -> assaillant -> nb de releves designe
VIVANT = defaultdict(lambda: defaultdict(int))   # acc -> assaillant -> nb de releves vivant
VISE_T = defaultdict(list)                       # acc -> (temps, defenseur, cible)
TIR_T = defaultdict(list)                        # acc -> (temps, defenseur)
IMP = defaultdict(set)

R_DEB = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|\d+\|\d+\|\d+\|(\d+)\|(\d+)')
R_FIN = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|(\d+)\|(\w+)')
R_POS = re.compile(r'HMT\|G\|POS\|(\d+)\|([\d.]+)\|(\d+)\|\d+\|\d+\|\d+\|(-?\d+)')
R_VIS = re.compile(r'HMT\|G\|VISE\|(\d+)\|([\d.]+)\|(\d+)\|(-?\d+)')
R_TIR = re.compile(r'HMT\|G\|TIR\|(\d+)\|([\d.]+)\|(\d+)\|')
R_IMP = re.compile(r'HMT\|G\|IMP\|(\d+)\|[\d.]+\|(\d+)\|(\d+)\|')

for l in open(J, errors='ignore'):
    m = R_POS.search(l)
    if m:
        a, h, ax = int(m.group(1)), int(m.group(3)), int(m.group(4))
        AXE[a][h] = ax
        if ax >= 0:
            VIVANT[a][h] += 1
        continue
    m = R_VIS.search(l)
    if m:
        VISE_T[int(m.group(1))].append((float(m.group(2)), int(m.group(3)), int(m.group(4))))
        continue
    m = R_TIR.search(l)
    if m:
        TIR_T[int(m.group(1))].append((float(m.group(2)), int(m.group(3))))
        continue
    m = R_IMP.search(l)
    if m:
        IMP[int(m.group(1))].add(int(m.group(3)))
        continue
    m = R_DEB.search(l)
    if m:
        D[int(m.group(1))] = dict(nDef=int(m.group(2)), axes=int(m.group(4)))
        continue
    m = R_FIN.search(l)
    if m:
        F[int(m.group(1))] = dict(duree=int(m.group(2)), cause=m.group(3))

for a, lst in VISE_T.items():
    for t_, d_, c_ in lst:
        if c_ >= 0 and AXE[a].get(d_) == -1 and AXE[a].get(c_, -1) >= 0:
            VISE[a][c_] += 1

clos = sorted(set(D) & set(F))
sain = [k for k in clos if F[k]['duree'] >= 30 and D[k]['nDef'] > 0]
dx = [k for k in sain if D[k]['axes'] == 2]
fr = [k for k in sain if D[k]['axes'] == 1]
print(f"\n  {len(clos)} accrochages clos · {len(sain)} retenus · deux_axes {len(dx)} · frontal {len(fr)}")


def stat(v):
    if not v:
        return 0.0, 0.0
    m = sum(v) / len(v)
    s = math.sqrt(sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1))
    return m, s


def welch(a, b):
    ma, sa = stat(a); mb, sb = stat(b)
    if len(a) < 2 or len(b) < 2:
        return 0.0, 1.0
    s = math.sqrt(sa * sa / len(a) + sb * sb / len(b))
    if s == 0:
        return ma - mb, 1.0
    return ma - mb, math.erfc(abs((ma - mb) / s) / math.sqrt(2))


def part_designes(ks):
    v = []
    for k in ks:
        att = [h for h, ax in AXE[k].items() if ax >= 0]
        if att:
            v.append(sum(1 for h in att if VISE[k].get(h, 0) > 0) / len(att))
    return v


def duree_designe(ks):
    v = []
    for k in ks:
        att = [h for h, ax in AXE[k].items() if ax >= 0 and VIVANT[k].get(h, 0) > 0]
        if att:
            v.append(sum(VISE[k].get(h, 0) / VIVANT[k][h] for h in att) / len(att))
    return v


def sans_tir(ks):
    v = []
    for k in ks:
        tirs = sorted(TIR_T.get(k, []))
        n = s = 0
        for t_, d_, c_ in VISE_T.get(k, []):
            if c_ < 0 or AXE[k].get(d_) != -1:
                continue
            n += 1
            if not any(abs(tt - t_) <= 4.0 and dd == d_ for tt, dd in tirs):
                s += 1
        if n:
            v.append(s / n)
    return v


print("\n" + "=" * 78)
print("  CONTROLES")
print("  " + "-" * 76)
avec = sum(1 for k in sain if VISE_T.get(k))
c1 = avec / max(len(sain), 1)
touche_des = tot_t = 0
for k in sain:
    for h in IMP.get(k, ()):
        if AXE[k].get(h, -1) >= 0:
            tot_t += 1
            touche_des += VISE[k].get(h, 0) > 0
c2 = touche_des / max(tot_t, 1)
print(f"     accrochages avec >= 1 releve VISE  {avec}/{len(sain)} = {c1:.1%}  (exige >= 95 %)"
      f"   -> {'OK' if c1 >= 0.95 else 'ECHEC'}")
print(f"     assaillants TOUCHES et designes    {touche_des}/{tot_t} = {c2:.1%}  (exige >= 80 %)"
      f"   -> {'OK' if c2 >= 0.80 else 'ECHEC'}")
if c1 < 0.95 or c2 < 0.80:
    print("\n  UN CONTROLE A CEDE — on ne lit pas les bras.")
    sys.exit(1)

res = {}
for nom, f_, seuil in (("A DESIGNATION", part_designes, 0.10),
                       ("B DUREE", duree_designe, 0.06),
                       ("C SANS TIR", sans_tir, None)):
    a, b = f_(dx), f_(fr)
    d, p = welch(a, b)
    res[nom] = (d, p)
    print("\n" + "=" * 78)
    print(f"  {nom}")
    print("  " + "-" * 76)
    print(f"     deux_axes {stat(a)[0]:6.1%}   frontal {stat(b)[0]:6.1%}")
    print(f"     ecart {d:+.1%} · p = {p:.4f}"
          + (f"   (seuil depose : {seuil:.0%})" if seuil else ""))

dB, pB = res["B DUREE"]
dC, _ = res["C SANS TIR"]
print("\n" + "=" * 78)
if dB <= -0.06 and pB < 0.05 and dC > 0:
    print("  ETABLI — LE SURSIS. Le deux-axes est designe MOINS LONGTEMPS, et ses designations")
    print("  sont plus souvent SANS TIR. Ils savent et ne peuvent pas tirer.")
elif dB >= 0 and dC <= 0:
    print("  MORT. Designe autant ou plus longtemps, et pas davantage de designations sans tir.")
    print("  Le mecanisme reste NON ETABLI et on cesse de le chercher de ce cote.")
else:
    print("  ZONE MIXTE. A, B et C ne concordent pas, ou l ecart reste sous la sensibilite.")
    print("  On garde les chiffres, ON N ECRIT PAS D HISTOIRE.")
print("  ⟨le flanc reste ferme dans les trois cas⟩")
print("  " + "=" * 76)
