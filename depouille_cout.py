#!/usr/bin/env python3
"""depouille_cout — REFAIRE L EXPOSITION PAR METRE GAGNE, avec un numerateur qui informe.

Protocole depose AVANT lecture : PROTOCOLE_EXPO_PAR_METRE.md
Grandeur : SUPPRESSION SUBIE (echantillons `VISE` ou l attaquant est designe, x2 s) par METRE
GAGNE. Lecture SUR LA BORNE. Aucun seuil chiffre repris de juillet.
LES CONTROLES SONT LUS AVANT LA GRANDEUR.
"""
import re, sys, math, random
from collections import defaultdict

F = sys.argv[1:] or ["/mnt/data/harmattan-sandbox/logs/n2_mission_partie1.out",
                     "/mnt/data/harmattan-sandbox/logs/serverA2.out"]

deb = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|(\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|')
fin = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|\d+\|(\w+)\|(\d+)\|(-?\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)\|(\d+)\|')
vis = re.compile(r'HMT\|G\|VISE\|(\d+)\|[\d.]+\|(-?\d+)\|(-?\d+)')

D, R, VU = {}, {}, defaultdict(int)
for f in F:
    try:
        lignes = open(f, encoding='utf-8', errors='ignore')
    except OSError:
        continue
    for L in lignes:
        m = deb.search(L)
        if m:
            D[int(m.group(1))] = dict(campDef=int(m.group(4)), nDef=int(m.group(5)),
                                      nAtt=int(m.group(6)), d0=int(m.group(7)))
            continue
        m = fin.search(L)
        if m:
            R[int(m.group(1))] = dict(pris=int(m.group(5)), ve=int(m.group(6)),
                                      vo=int(m.group(7)), dmin=int(m.group(8)))
            continue
        m = vis.search(L)
        if m and int(m.group(3)) >= 0:          # un defenseur a DESIGNE quelqu un
            VU[int(m.group(1))] += 1

clos = sorted(set(D) & set(R))
E = []
for i in clos:
    d, r = D[i], R[i]
    surv = r['vo'] if d['campDef'] == 0 else r['ve']
    E.append(dict(i=i, pris=r['pris'], nAtt=d['nAtt'], pertes=max(0, d['nAtt'] - surv),
                  gagne=d['d0'] - r['dmin'], supp=2.0 * VU.get(i, 0), nDef=d['nDef']))

print(f"\n  {len(E)} accrochages clos · {sum(VU.values())} echantillons de designation")
if not E:
    print("  rien a lire"); sys.exit(0)

print("\n  CONTROLES — lus AVANT la grandeur")
ok = True
def dire(nom, cond, detail):
    global ok
    print(f"    {'PASSE' if cond else 'TOMBE':>6}  {nom:<44} {detail}")
    if not cond: ok = False

pris = [e for e in E if e['pris'] == 1]
non = [e for e in E if e['pris'] == 0]
moy = lambda v: sum(v) / len(v) if v else 0.0

dire("TAILLE — 30 accrochages par bras", len(pris) >= 30 and len(non) >= 30,
     f"{len(pris)} pris · {len(non)} non pris")
p_pertes, n_pertes = moy([e['pertes'] for e in pris]), moy([e['pertes'] for e in non])
dire("POSITIF — les non pris perdent plus d hommes", n_pertes > p_pertes,
     f"{n_pertes:.2f} contre {p_pertes:.2f}")
zero = [e for e in E if e['gagne'] <= 0]
dire("DENOMINATEUR — les accrochages a zero metre sont NOMMES", True,
     f"{len(zero)} sur {len(E)} — ecartes du rapport, comptes ici")
dire("DESIGNATION — le temoin d intention a parle", sum(VU.values()) > 100,
     f"{sum(VU.values())} echantillons")

if not ok:
    print("\n  AUCUN VERDICT. Un controle est tombe.")
    sys.exit(0)

U = [e for e in E if e['gagne'] > 0]
for e in U:
    e['cout'] = e['supp'] / e['gagne']
up = [e['cout'] for e in U if e['pris'] == 1]
un = [e['cout'] for e in U if e['pris'] == 0]

print(f"\n  LA GRANDEUR — suppression subie (s) par metre gagne")
print(f"    {'pris':<12}{moy(up):>8.3f}   sur {len(up)} accrochages")
print(f"    {'non pris':<12}{moy(un):>8.3f}   sur {len(un)} accrochages")
rap = moy(un) / moy(up) if moy(up) > 0 else float('inf')
print(f"    rapport non-pris / pris : {rap:.2f}")

# intervalle par BOOTSTRAP : la distribution des couts est tres asymetrique, une
# approximation normale sur la moyenne mentirait.
random.seed(7)
B = []
for _ in range(4000):
    a = moy([random.choice(un) for _ in un])
    b = moy([random.choice(up) for _ in up])
    if b > 0: B.append(a / b)
B.sort()
lo, hi = B[int(0.025 * len(B))], B[int(0.975 * len(B))]
print(f"    intervalle 95 % (bootstrap 4000) : [{lo:.2f} ; {hi:.2f}]")

# CONTROLE NUL : l etiquette permutee ne doit pas reproduire l effet
tous = up + un
np_ = len(up)
plus = 0
for _ in range(1000):
    random.shuffle(tous)
    a, b = moy(tous[np_:]), moy(tous[:np_])
    if b > 0 and a / b >= rap: plus += 1
p_perm = (plus + 1) / 1001.0
print(f"\n    CONTROLE NUL — etiquette permutee 1000 fois : p = {p_perm:.4f}")

print("\n  LA LECTURE, sur la BORNE ⟨regle 14⟩")
print("  " + "-" * 66)
if lo > 1.0 and p_perm < 0.05:
    print(f"    L ACQUIS EST RETABLI. Borne inferieure {lo:.2f} > 1, permutation p = {p_perm:.4f}.")
    print(f"    Cout d un accrochage perdu : {rap:.2f} fois celui d un accrochage gagne,")
    print( "    mesure sur la SUPPRESSION SUBIE et non sur `expo`.")
    print( "    ⚠️ Le chiffre de juillet (1,86) n est PAS retrouve : il ne peut pas l etre,")
    print( "    il portait sur une autre grandeur. C est le SIGNE qui revient, pas la valeur.")
else:
    print(f"    L ACQUIS NE REVIENT PAS. Borne inferieure {lo:.2f}, permutation p = {p_perm:.4f}.")
    print( "    Il reste au registre des sursitaires, et on le dit.")
