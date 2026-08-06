#!/usr/bin/env python3
"""temoin_tir.py — ORDRE 3 : « ils SAVENT, et ils ne peuvent pas TIRER » ?

Criteres deposes AVANT ce comptage : CRITERES_TEMOIN_TIR.md (commit e738b6a). Rappel des
seuils, recopies sans retouche :

  ETABLIE     le deux_axes est designe cible SIGNIFICATIVEMENT MOINS (p < 0,05, ecart >= 8
              points), et les impacts vont dans le meme sens.
  MORTE       designe autant ou plus, ET touche autant ou plus.
  ZONE MIXTE  intention et impact se contredisent, ou l ecart reste sous 8 points
              -> on garde les chiffres, on n ecrit PAS d histoire.

SENSIBILITE, ecrite avant : avec 160 accrochages deux_axes et 140 frontal, ce corpus voit un
ecart d environ 8 points ou plus. En dessous, un « non significatif » ne veut rien dire.

LECTURE AU NIVEAU DE L ACCROCHAGE, jamais de l homme : les hommes d un meme accrochage ne
sont pas independants, et compter par homme gonflerait l effectif d un facteur dix.
"""
import re, sys, math
from collections import defaultdict

J = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA_a2.out'

D, F = {}, {}
AXE = defaultdict(dict)        # acc -> {homme: axe}   (-1 = defenseur)
DERNIER = defaultdict(dict)    # acc -> {homme: derniere date vu vivant}
FIN_T = {}                     # acc -> date de fin
DESIGNE = defaultdict(set)     # acc -> hommes designes cible PAR UN DEFENSEUR
TOUCHE = defaultdict(set)      # acc -> hommes touches PAR UN DEFENSEUR
ARRIVE = defaultdict(set)      # acc -> axes arrives

R_DEB = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|\d+\|\d+\|\d+\|(\d+)\|(\d+)')
R_FIN = re.compile(r'HMT\|G\|fin\|(\d+)\|([\d.]+)\|(\d+)\|(\w+)\|\d+\|\d+\|(\d+)\|\d+\|\d+\|\d+\|(\d+)\|')
R_POS = re.compile(r'HMT\|G\|POS\|(\d+)\|([\d.]+)\|(\d+)\|\d+\|\d+\|\d+\|(-?\d+)')
R_TIR = re.compile(r'HMT\|G\|TIR\|(\d+)\|[\d.]+\|(\d+)\|(-?\d+)')
R_IMP = re.compile(r'HMT\|G\|IMP\|(\d+)\|[\d.]+\|(\d+)\|(\d+)\|')

tir_brut, imp_brut = [], []
for l in open(J, errors='ignore'):
    m = R_DEB.search(l)
    if m:
        D[int(m.group(1))] = dict(nDef=int(m.group(2)), nAtt=int(m.group(3)),
                                  axes=int(m.group(4)), fige=int(m.group(5)))
        continue
    m = R_FIN.search(l)
    if m:
        F[int(m.group(1))] = dict(duree=int(m.group(3)), cause=m.group(4), pris=int(m.group(5)))
        FIN_T[int(m.group(1))] = float(m.group(2))
        continue
    m = R_POS.search(l)
    if m:
        a, t, h, ax = int(m.group(1)), float(m.group(2)), int(m.group(3)), int(m.group(4))
        AXE[a][h] = ax
        DERNIER[a][h] = t
        continue
    m = R_TIR.search(l)
    if m:
        tir_brut.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        continue
    m = R_IMP.search(l)
    if m:
        imp_brut.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))

# un defenseur se reconnait a son axe : -1 dans POS. On ne garde que les tirs DEFENSEUR->ASSAILLANT.
for a, tireur, cible in tir_brut:
    if cible >= 0 and AXE[a].get(tireur) == -1 and AXE[a].get(cible, -1) >= 0:
        DESIGNE[a].add(cible)
for a, tireur, victime in imp_brut:
    if AXE[a].get(tireur) == -1 and AXE[a].get(victime, -1) >= 0:
        TOUCHE[a].add(victime)

clos = sorted(set(D) & set(F))
sain = [k for k in clos if F[k]['duree'] >= 30 and D[k]['nDef'] > 0]
print(f"\n  {len(clos)} accrochages clos · {len(sain)} retenus apres filtre de sante")


def moyennes(ks, ens):
    """part d assaillants concernes, MOYENNEE PAR ACCROCHAGE."""
    v = []
    for k in ks:
        att = [h for h, ax in AXE[k].items() if ax >= 0]
        if att:
            v.append(len(ens[k] & set(att)) / len(att))
    return v


def welch(a, b):
    if len(a) < 2 or len(b) < 2:
        return 0.0, 1.0
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    va = sum((x-ma)**2 for x in a)/(len(a)-1)
    vb = sum((x-mb)**2 for x in b)/(len(b)-1)
    s = math.sqrt(va/len(a) + vb/len(b))
    if s == 0:
        return ma-mb, 1.0
    t = (ma-mb)/s
    return ma-mb, math.erfc(abs(t)/math.sqrt(2))


print("\n" + "=" * 78)
print("  CONTROLE DE COHERENCE — a passer AVANT de lire les bras")
print("  " + "-" * 76)
# 1. les MORTS doivent etre touches a ~100 %. Un mort = un assaillant dont la derniere
#    position vivante precede la fin de l accrochage de plus de 15 s (POS ne logue que les vivants).
morts, morts_touches = 0, 0
for k in sain:
    for h, ax in AXE[k].items():
        if ax >= 0 and FIN_T.get(k, 0) - DERNIER[k].get(h, 0) > 15:
            morts += 1
            if h in TOUCHE[k]:
                morts_touches += 1
tx_m = morts_touches / max(morts, 1)
ok_c1 = tx_m >= 0.90
print(f"     assaillants morts touches      {morts_touches}/{morts} = {tx_m:.1%}"
      f"  (exige >= 90 %)   -> {'OK' if ok_c1 else 'ECHEC'}")
# 2. au moins un designe dans la grande majorite des accrochages
avec = sum(1 for k in sain if DESIGNE[k])
ok_c2 = avec / max(len(sain), 1) >= 0.90
print(f"     accrochages avec >= 1 designe  {avec}/{len(sain)} = {avec/max(len(sain),1):.1%}"
      f"  (exige >= 90 %)   -> {'OK' if ok_c2 else 'ECHEC'}")

if not (ok_c1 and ok_c2):
    print("\n  LE DEPOUILLEUR EST CASSE. Une banalite est fausse — on ne lit pas les bras.")
    raise SystemExit(1)

print("\n" + "=" * 78)
print("  TEMOIN D INTENTION — part d assaillants DESIGNES cible par un defenseur")
print("  " + "-" * 76)
dx = [k for k in sain if D[k]['axes'] == 2]
fr = [k for k in sain if D[k]['axes'] == 1]
a, b = moyennes(dx, DESIGNE), moyennes(fr, DESIGNE)
print(f"     deux_axes  {sum(a)/max(len(a),1):6.1%}   ({len(a)} accrochages)")
print(f"     frontal    {sum(b)/max(len(b),1):6.1%}   ({len(b)} accrochages)")
d1, p1 = welch(a, b)
print(f"     ecart {d1:+.1%} · p = {p1:.4f}"
      f"   ⟨la porte voit ~8 points ; en dessous, un p eleve ne dit RIEN⟩")

print("\n" + "=" * 78)
print("  TEMOIN D IMPACT — part d assaillants TOUCHES par un defenseur")
print("  " + "-" * 76)
c, e = moyennes(dx, TOUCHE), moyennes(fr, TOUCHE)
print(f"     deux_axes  {sum(c)/max(len(c),1):6.1%}")
print(f"     frontal    {sum(e)/max(len(e),1):6.1%}")
d2, p2 = welch(c, e)
print(f"     ecart {d2:+.1%} · p = {p2:.4f}")

print("\n" + "=" * 78)
moins_designe = d1 <= -0.08 and p1 < 0.05
plus_designe = d1 >= 0
if moins_designe and d2 < 0:
    print("  HYPOTHESE ETABLIE. Le deux-axes est VU davantage et ENGAGE moins : ils savent et")
    print("  ne peuvent pas tirer. Le mecanisme est le SURSIS.")
    print("  -> l etage 1 doit porter le risque d ENGAGEMENT, pas le risque d etre vu.")
elif plus_designe and d2 >= 0:
    print("  HYPOTHESE MORTE. Le deux-axes est designe autant ou plus, ET touche autant ou plus.")
    print("  Le mecanisme reste NON ETABLI, et on cesse de le chercher de ce cote.")
else:
    print("  ZONE MIXTE. Intention et impact ne concordent pas, ou l ecart reste sous la")
    print("  sensibilite de la porte. On garde les chiffres, on N ECRIT PAS D HISTOIRE.")
    print("  -> l etage 1 part sur le risque appris tel quel, sans reorientation.")
print("  ⟨dans les trois cas : le flanc reste ferme, aucune nuit de plus de ce cote⟩")
print("  " + "=" * 76)
