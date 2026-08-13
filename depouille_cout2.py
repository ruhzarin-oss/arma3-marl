#!/usr/bin/env python3
"""depouille_cout2 — L EXPOSITION PAR METRE GAGNE, deuxieme dépouillement.

Protocole depose AVANT mesure : PROTOCOLE_COUT_V2.md
Grandeur : SUPPRESSION SUBIE (echantillons `VISE` ou l homme est DESIGNE, x2 s) par METRE
GAGNE, PAR HOMME. Lecture SUR LA BORNE. Aucun seuil chiffre repris de juillet.

⚠️ LA v1 A RENDU UN VERDICT SUR UN DENOMINATEUR QUI NE MESURAIT PAS CE QU IL NOMMAIT. Elle
prenait `_dmin` du journal pour « distance a l objectif » ; c est la distance minimale a un
defenseur VIVANT, et la boucle qui l entretient s arrete quand la defense tombe — d ou 3935 m
sur une prise reussie et 168 accrochages PRIS declares « a gain nul ». Aucun de ses quatre
controles ne demandait si un champ MESURE LA CHOSE QU IL NOMME. C est le premier controle ici.
"""
import re, sys, math, random
from collections import defaultdict
from cles import Segmenteur

F = sys.argv[1:] or ["/mnt/data/harmattan-sandbox/logs/pause_12-08_soir/serverCT.out"]

deb = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|(\d+)\|')
fin = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|\d+\|(\w+)\|(\d+)\|(-?\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)\|')
pos = re.compile(r'HMT\|G\|POS\|(\d+)\|[\d.]+\|(-?\d+)\|(\d+)')
vis = re.compile(r'HMT\|G\|VISE\|(\d+)\|[\d.]+\|-?\d+\|(-?\d+)')

seg = Segmenteur()
D, R = {}, {}
P = defaultdict(lambda: defaultdict(list))     # accrochage -> homme -> [distances]
V = defaultdict(lambda: defaultdict(int))      # accrochage -> homme -> designations
for f in F:
    for L in open(f, encoding='utf-8', errors='ignore'):
        m = deb.search(L)
        if m:
            D[seg.cle(f, int(m.group(1)))] = dict(campDef=int(m.group(2)), nDef=int(m.group(3)),
                                                  nAtt=int(m.group(4)))
            continue
        m = fin.search(L)
        if m:
            R[seg.cle_passive(f, int(m.group(1)))] = dict(pris=int(m.group(5)),
                                                          ve=int(m.group(6)), vo=int(m.group(7)))
            continue
        m = pos.search(L)
        if m:
            P[seg.cle_passive(f, int(m.group(1)))][int(m.group(2))].append(int(m.group(3)))
            continue
        m = vis.search(L)
        if m and int(m.group(2)) >= 0:
            V[seg.cle_passive(f, int(m.group(1)))][int(m.group(2))] += 1

clos = [k for k in D if k in R and k in P]
print(f"\n  {len(clos)} accrochages clos AVEC positions · {sum(len(v) for v in P.values())} hommes suivis")
if not clos:
    print("  rien a lire"); sys.exit(0)

E = []
for k in clos:
    d, r = D[k], R[k]
    surv = r['vo'] if d['campDef'] == 0 else r['ve']
    hommes = []
    for h, dist in P[k].items():
        if len(dist) < 2: continue
        gagne = dist[0] - min(dist)
        hommes.append(dict(h=h, gagne=gagne, supp=2.0 * V[k].get(h, 0),
                           d0=dist[0], dmin=min(dist), n=len(dist)))
    if hommes:
        E.append(dict(k=k, pris=r['pris'], pertes=max(0, d['nAtt'] - surv), hommes=hommes))

print("\n  CONTROLES — lus AVANT la grandeur")
ok = True
def dire(nom, cond, detail):
    global ok
    print(f"    {'PASSE' if cond else 'TOMBE':>6}  {nom:<46} {detail}")
    if not cond: ok = False

moy = lambda v: sum(v) / len(v) if v else 0.0
pris = [e for e in E if e['pris'] == 1]
non = [e for e in E if e['pris'] == 0]

# ─── LE CONTROLE QUI MANQUAIT A LA v1
mauvais = [e for e in pris if max(h['gagne'] for h in e['hommes']) <= 0]
dire("SENS — un accrochage PRIS a gagne des metres", not mauvais,
     f"{len(mauvais)} pris a gain nul sur {len(pris)}")
descend = sum(1 for e in E for h in e['hommes'] if h['dmin'] < h['d0'])
total_h = sum(len(e['hommes']) for e in E)
dire("SENS — la distance DECROIT au fil du temps",
     total_h and descend / total_h > 0.7, f"{100*descend/max(total_h,1):.0f} % des hommes se rapprochent")
dire("POSITIF — les non pris perdent plus d hommes",
     moy([e['pertes'] for e in non]) > moy([e['pertes'] for e in pris]),
     f"{moy([e['pertes'] for e in non]):.2f} contre {moy([e['pertes'] for e in pris]):.2f}")
dire("TAILLE — 30 accrochages par bras", len(pris) >= 30 and len(non) >= 30,
     f"{len(pris)} pris · {len(non)} non pris")
zero = [h for e in E for h in e['hommes'] if h['gagne'] <= 0]
dire("DENOMINATEUR — les hommes a zero metre sont NOMMES", True,
     f"{len(zero)} sur {total_h} — ecartes du rapport, comptes ici")

if not ok:
    print("\n  AUCUN VERDICT. Un controle est tombe — on ne lit rien d autre.")
    sys.exit(0)

for e in E:
    c = [h['supp'] / h['gagne'] for h in e['hommes'] if h['gagne'] > 0]
    e['cout'] = moy(c) if c else None
U = [e for e in E if e['cout'] is not None]
up = [e['cout'] for e in U if e['pris'] == 1]
un = [e['cout'] for e in U if e['pris'] == 0]
print(f"\n  LA GRANDEUR — suppression subie (s) par metre gagne, PAR HOMME")
print(f"    {'pris':<12}{moy(up):>8.3f}   sur {len(up)} accrochages")
print(f"    {'non pris':<12}{moy(un):>8.3f}   sur {len(un)} accrochages")
rap = moy(un) / moy(up) if moy(up) > 0 else float('inf')
print(f"    rapport non-pris / pris : {rap:.2f}")

random.seed(7)
B = []
for _ in range(4000):
    a = moy([random.choice(un) for _ in un]); b = moy([random.choice(up) for _ in up])
    if b > 0: B.append(a / b)
B.sort()
lo, hi = B[int(0.025 * len(B))], B[int(0.975 * len(B))]
print(f"    intervalle 95 % (bootstrap 4000) : [{lo:.2f} ; {hi:.2f}]")

tous = up + un; npx = len(up); plus = 0
for _ in range(1000):
    random.shuffle(tous)
    a, b = moy(tous[npx:]), moy(tous[:npx])
    if b > 0 and a / b >= rap: plus += 1
p_perm = (plus + 1) / 1001.0
print(f"\n    CONTROLE NUL — etiquette permutee 1000 fois : p = {p_perm:.4f}")

print("\n  LA LECTURE, sur la BORNE ⟨regle 14⟩")
print("  " + "-" * 68)
if lo > 1.0 and p_perm < 0.05:
    print(f"    L ACQUIS EST RETABLI. Borne inferieure {lo:.2f} > 1, permutation p = {p_perm:.4f}.")
    print(f"    Un accrochage perdu coute {rap:.2f} fois un accrochage gagne, mesure sur la")
    print( "    SUPPRESSION SUBIE et non sur `expo`.")
    print( "    ⚠️ Le 1,86 de juillet n est PAS retrouve et ne peut pas l etre : autre grandeur.")
    print( "    C est le SIGNE qui revient, pas la valeur. ⟨Fable : le signe se transporte⟩")
else:
    print(f"    L ACQUIS NE REVIENT PAS. Borne {lo:.2f}, permutation p = {p_perm:.4f}.")
    print( "    Il reste au registre des sursitaires, et on le dit.")
