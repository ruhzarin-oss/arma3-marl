#!/usr/bin/env python3
"""temoin_feu.py — ORDRE 10 : le deux-axes RECOIT-IL MOINS DE FEU, alors qu il est VU PLUS ?

Criteres deposes AVANT ce comptage : CRITERES_FEU_RECU.md. Rappel sans retouche :

  A  FEU RECU      part d assaillants pris pour cible par un defenseur, moyenne PAR ACCROCHAGE
  B  IMPACTS RECUS part d assaillants touches, meme moyenne
  C  MUETS         part d accrochages sans aucun tir defenseur, PAR BRAS + duree par bras

  ETABLI  A significativement moins (p < 0,05, ecart >= 10 pts), coherent sur B
  MORT    A et B egaux ou superieurs
  MIXTE   A et B se contredisent, ou l ecart reste sous 10 points -> pas d histoire

SENSIBILITE ecrite avant : ~10 points. Le script IMPRIME la dispersion reellement observee ;
si elle depasse nettement 0,30, la porte est moins sensible que prevu et il le dit AVANT les bras.

CONTROLES qui gardent le droit de tout arreter :
  1. les morts touches a >= 90 %  (un mort = POS cesse de l ecrire, il ne logue que les vivants)
  2. >= 60 % des accrochages avec au moins un tir defenseur — seuil fixe sur la COUVERTURE
     REELLE de l instrument, mesuree, et non sur une attente inventee : c est l erreur qu on corrige.
"""
import re, sys, math
from collections import defaultdict

J = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA_a2.out'

D, F, FIN_T = {}, {}, {}
AXE = defaultdict(dict)
DERNIER = defaultdict(dict)
FEU = defaultdict(set)          # acc -> assaillants pris pour cible par un defenseur
TOUCHE = defaultdict(set)
TIR_DEF = defaultdict(int)      # acc -> nb de tirs defenseur (cible ou non)

R_DEB = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|\d+\|\d+\|\d+\|(\d+)\|(\d+)')
R_FIN = re.compile(r'HMT\|G\|fin\|(\d+)\|([\d.]+)\|(\d+)\|(\w+)')
R_POS = re.compile(r'HMT\|G\|POS\|(\d+)\|([\d.]+)\|(\d+)\|\d+\|\d+\|\d+\|(-?\d+)')
R_TIR = re.compile(r'HMT\|G\|TIR\|(\d+)\|[\d.]+\|(\d+)\|(-?\d+)')
R_IMP = re.compile(r'HMT\|G\|IMP\|(\d+)\|[\d.]+\|(\d+)\|(\d+)\|')

tirs, imps = [], []
for l in open(J, errors='ignore'):
    m = R_POS.search(l)
    if m:
        a, t, h, ax = int(m.group(1)), float(m.group(2)), int(m.group(3)), int(m.group(4))
        AXE[a][h] = ax
        DERNIER[a][h] = t
        continue
    m = R_TIR.search(l)
    if m:
        tirs.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        continue
    m = R_IMP.search(l)
    if m:
        imps.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        continue
    m = R_DEB.search(l)
    if m:
        D[int(m.group(1))] = dict(nDef=int(m.group(2)), nAtt=int(m.group(3)),
                                  axes=int(m.group(4)), fige=int(m.group(5)))
        continue
    m = R_FIN.search(l)
    if m:
        F[int(m.group(1))] = dict(duree=int(m.group(3)), cause=m.group(4))
        FIN_T[int(m.group(1))] = float(m.group(2))

for a, tireur, cible in tirs:
    if AXE[a].get(tireur) == -1:                       # le tireur est un defenseur
        TIR_DEF[a] += 1
        if cible >= 0 and AXE[a].get(cible, -1) >= 0:
            FEU[a].add(cible)
for a, tireur, victime in imps:
    if AXE[a].get(tireur) == -1 and AXE[a].get(victime, -1) >= 0:
        TOUCHE[a].add(victime)

clos = sorted(set(D) & set(F))
sain = [k for k in clos if F[k]['duree'] >= 30 and D[k]['nDef'] > 0]
print(f"\n  {len(clos)} accrochages clos · {len(sain)} retenus apres filtre de sante")

dx = [k for k in sain if D[k]['axes'] == 2]
fr = [k for k in sain if D[k]['axes'] == 1]


def parts(ks, ens):
    v = []
    for k in ks:
        att = [h for h, ax in AXE[k].items() if ax >= 0]
        if att:
            v.append(len(ens[k] & set(att)) / len(att))
    return v


def stat(v):
    if not v:
        return 0.0, 0.0
    m = sum(v) / len(v)
    s = math.sqrt(sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1))
    return m, s


def welch(a, b):
    ma, sa = stat(a)
    mb, sb = stat(b)
    if len(a) < 2 or len(b) < 2:
        return 0.0, 1.0
    s = math.sqrt(sa * sa / len(a) + sb * sb / len(b))
    if s == 0:
        return ma - mb, 1.0
    return ma - mb, math.erfc(abs((ma - mb) / s) / math.sqrt(2))


print("\n" + "=" * 78)
print("  CONTROLES — ils gardent le droit de tout arreter")
print("  " + "-" * 76)
morts = mt = 0
for k in sain:
    for h, ax in AXE[k].items():
        if ax >= 0 and FIN_T.get(k, 0) - DERNIER[k].get(h, 0) > 15:
            morts += 1
            mt += h in TOUCHE[k]
c1 = mt / max(morts, 1)
avec = sum(1 for k in sain if TIR_DEF[k])
c2 = avec / max(len(sain), 1)
print(f"     morts touches                  {mt}/{morts} = {c1:.1%}   (exige >= 90 %)"
      f"   -> {'OK' if c1 >= 0.90 else 'ECHEC'}")
print(f"     accrochages avec feu defenseur {avec}/{len(sain)} = {c2:.1%}   (exige >= 60 %)"
      f"   -> {'OK' if c2 >= 0.60 else 'ECHEC'}")
if c1 < 0.90 or c2 < 0.60:
    print("\n  UN CONTROLE A CEDE — on ne lit pas les bras.")
    raise SystemExit(1)

A_dx, A_fr = parts(dx, FEU), parts(fr, FEU)
B_dx, B_fr = parts(dx, TOUCHE), parts(fr, TOUCHE)
disp = max(stat(A_dx)[1], stat(A_fr)[1])
print(f"\n     dispersion observee sur A : {disp:.3f}   (prevue 0,30)"
      f"   -> porte {'conforme' if disp <= 0.35 else 'MOINS SENSIBLE QUE PREVU'}")
if disp > 0.35:
    print("     ⟨l ecart minimal visible est donc plus grand que les 10 points annonces⟩")

print("\n" + "=" * 78)
print("  A — FEU RECU   (part d assaillants pris pour cible par un defenseur)")
print("  " + "-" * 76)
for nom, v in (('deux_axes', A_dx), ('frontal', A_fr)):
    m, s = stat(v)
    print(f"     {nom:12s} {m:6.1%}   (ecart-type {s:.3f} · {len(v)} accrochages)")
dA, pA = welch(A_dx, A_fr)
print(f"     ecart {dA:+.1%} · p = {pA:.4f}   (exige <= -10 pts et p < 0,05 pour ETABLI)")

print("\n" + "=" * 78)
print("  B — IMPACTS RECUS")
print("  " + "-" * 76)
for nom, v in (('deux_axes', B_dx), ('frontal', B_fr)):
    m, s = stat(v)
    print(f"     {nom:12s} {m:6.1%}   (ecart-type {s:.3f})")
dB, pB = welch(B_dx, B_fr)
print(f"     ecart {dB:+.1%} · p = {pB:.4f}")

print("\n" + "=" * 78)
print("  C — ACCROCHAGES MUETS   (aucun tir defenseur) + duree, par bras")
print("  " + "-" * 76)
for nom, ks in (('deux_axes', dx), ('frontal', fr)):
    muets = [k for k in ks if not TIR_DEF[k]]
    dur = sorted(F[k]['duree'] for k in ks)
    med = dur[len(dur) // 2] if dur else 0
    print(f"     {nom:12s} muets {len(muets):3d}/{len(ks):3d} = {len(muets)/max(len(ks),1):5.1%}"
          f"   · duree mediane {med:3d} s")

print("\n" + "=" * 78)
etabli = dA <= -0.10 and pA < 0.05 and dB < 0
mort = dA >= 0 and dB >= 0
if etabli:
    print("  ETABLI — LE SURSIS. Le deux-axes est VU davantage (+6,6 pts, acquis) et RECOIT")
    print("  MOINS DE FEU. Ils savent et ne peuvent pas tirer.")
    print("  -> l etage 1 doit porter le risque d ENGAGEMENT, pas le risque d etre vu.")
elif mort:
    print("  MORT. Le deux-axes recoit autant ou plus de feu, et autant ou plus d impacts.")
    print("  L hypothese tombe. Le mecanisme reste NON ETABLI et on cesse de le chercher ici.")
else:
    print("  ZONE MIXTE. A et B ne concordent pas, ou l ecart reste sous la sensibilite de la")
    print("  porte. On garde les chiffres, ON N ECRIT PAS D HISTOIRE.")
    print("  -> l etage 1 part sans reorientation ; le re-run echantillonne se decide a la")
    print("     regle deposee (CPU libre et etage 1 non gene).")
print("  ⟨dans les trois cas : le flanc reste ferme, aucune nuit de plus de ce cote⟩")
print("  " + "=" * 76)
