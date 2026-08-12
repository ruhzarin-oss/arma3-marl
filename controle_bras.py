#!/usr/bin/env python3
"""controle_bras.py — LE CONTROLE PAR BRAS DU GESTE N°1, PAYE SUR LES DONNEES DEJA TOMBEES.

⟨Fable, 09/08⟩ « L appariement intra-session achete l immunite a ce que la session fait aux
DEUX bras egalement ; il n achete RIEN contre ce qu elle fait a UN SEUL bras. Aucune admission
de terrain ne couvrira jamais ce second mal — seul un controle positif par bras le fait. Ne
crois pas le geste n°1 protege par construction : son pile ou face cacherait tout aussi bien
une session ou un bras est silencieusement mort. Verifie s il porte un controle de bras ;
sinon, ses 788 accrochages ont la meme dette. »

LE GENERATEUR N EN PORTE PAS. Le professeur a un controle implicite — ses lignes `BOND`
disparaitraient s il mourait — mais le TEMOIN n a rien qui atteste qu il s est comporte en
temoin.

MAIS LA DETTE EST PAYABLE SANS RELANCER : les positions sont journalisees a 1 Hz. On reconstruit
donc le controle APRES COUP, sur les accrochages deja tombes.

⚠️ ET LE PREMIER JET ETAIT UN PROXY. Il demandait « les hommes ont-ils avance de plus de 50 m ».
Or LE BOND AVANCE PLUS LENTEMENT PAR DEFINITION — une equipe sur deux est arretee a chaque
instant. Le controle confondait donc « le bras a joue » avec « le bras a avance », sur un geste
dont l objet meme est d avancer autrement : professeur 54 %, temoin 73 %, et rien pour dire si
l ecart etait la panne ou le geste. ⟨regle 6 : verifie la propriete que le MECANISME utilise⟩

LE CONTROLE DIRECT EXISTE ET IL EST GRATUIT : le journal `BOND` ne s ecrit QUE dans le bras
professeur, une ligne par bond. Zero bond dans un accrochage professeur = le professeur n a pas
joue, quelle que soit la distance parcourue. C est la propriete que le mecanisme utilise.

CE QUE LE CONTROLE DEMANDE, par accrochage et par bras :
  · LES HOMMES ONT AVANCE — la distance a l objectif diminue franchement entre le debut et la
    fin. Un bras dont les hommes ne progressent pas n a pas joue, quelle que soit la raison.
  · ILS ETAIENT ASSEZ NOMBREUX — au moins 6 hommes vus dans le journal.

ET CE QUI SERAIT UNE PANNE : un bras dont la part d accrochages « qui avancent » s effondre
alors que l autre tient. C est exactement ce que le pile ou face masquerait.
"""
import re, sys
from collections import defaultdict

F = '/mnt/data/harmattan-sandbox/logs/serverBA.out'
pos  = re.compile(r'HMT\|G\|POS\|(\d+)\|([\d.]+)\|(-?\d+)\|(\d+)\|(\d+)\|')
bond = re.compile(r'HMT\|G\|BOND\|(\d+)\|')
lieu = re.compile(r'HMT\|G\|LIEU\|(\d+)\|(\d+)\|(\d+)')

bras, couloir = {}, {}
prem, dern, hommes, bonds = {}, {}, defaultdict(set), {}
for L in open(F, encoding='utf-8', errors='ignore'):
    m = lieu.search(L)
    if m:
        bras[int(m.group(1))] = int(m.group(3)); couloir[int(m.group(1))] = int(m.group(2))
        continue
    m = pos.search(L)
    if m:
        i, t, u, x, y = int(m.group(1)), float(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        if i not in prem: prem[i] = (t, x, y)
        dern[i] = (t, x, y)
        hommes[i].add(u)
        continue
    m = bond.search(L)
    if m:
        bonds[int(m.group(1))] = bonds.get(int(m.group(1)), 0) + 1

# l objectif d un accrochage : le point vers lequel tout le monde converge. On le prend comme
# la position la plus AVANCEE atteinte, faute de le journaliser — approximation assumee, mais
# elle suffit a repondre « ces hommes ont-ils avance ? »
avance = {}
for i in prem:
    if i not in dern: continue
    (t0, x0, y0), (t1, x1, y1) = prem[i], dern[i]
    avance[i] = ((x1-x0)**2 + (y1-y0)**2) ** 0.5

clos = sorted(set(bras) & set(avance))
if len(clos) > 1: clos = clos[:-1]          # le dernier accrochage est encore ouvert
print(f"\n  {len(clos)} accrochages clos et positionnes")
print(f"\n  {'bras':<22}{'n':>6}{'ont avance >50 m':>20}{'hommes vus (median)':>22}")
print("  " + "-" * 70)
etat = {}
for b, nom in ((1, 'professeur (bond)'), (0, 'temoin (simultane)')):
    ids = [i for i in clos if bras[i] == b]
    if not ids: continue
    ok = sum(1 for i in ids if avance[i] > 50)
    h = sorted(len(hommes[i]) for i in ids)
    med = h[len(h)//2] if h else 0
    etat[b] = 100.0 * ok / len(ids)
    print(f"  {nom:<22}{len(ids):>6}{('%d  (%.0f %%)' % (ok, 100.0*ok/len(ids))):>20}{med:>22}")
print("  " + "-" * 70)

# ─── LE CONTROLE DIRECT : le professeur a-t-il REELLEMENT bondi ?
prof = [i for i in clos if bras[i] == 1]
tem  = [i for i in clos if bras[i] == 0]
joue = sum(1 for i in prof if bonds.get(i, 0) > 0)
fuite = sum(1 for i in tem if bonds.get(i, 0) > 0)
nb = sorted(bonds.get(i, 0) for i in prof)
print(f"\n  LE CONTROLE DIRECT — le journal BOND, qui ne s ecrit QUE chez le professeur")
print(f"    professeur qui a REELLEMENT bondi : {joue} sur {len(prof)}  ({100.0*joue/max(1,len(prof)):.0f} %)")
print(f"    bonds par accrochage (median)      : {nb[len(nb)//2] if nb else 0}")
print(f"    CONTROLE NUL — bonds dans le TEMOIN : {fuite} sur {len(tem)}  (doit valoir 0)")
if joue == len(prof) and fuite == 0:
    print("    -> les deux bras ont joue leur role, accrochage par accrochage. C est LA")
    print("       propriete que le mecanisme utilise, pas un proxy de distance.")
else:
    print("    -> ⚠️ UN BRAS N A PAS JOUE SON ROLE dans certains accrochages. Ces accrochages")
    print("       sont a ecarter du verdict, et leur nombre est a dire a voix haute.")

if len(etat) == 2:
    d = abs(etat[1] - etat[0])
    print(f"\n  ECART ENTRE LES DEUX BRAS : {d:.0f} points de pourcentage")
    if min(etat.values()) < 50:
        print("  ⚠️ UN BRAS NE JOUE PAS. Moins d un accrochage sur deux y voit les hommes")
        print("     avancer — le banc mesure un bras mort contre un bras vivant.")
    elif d > 20:
        print("  ⚠️ LES DEUX BRAS NE JOUENT PAS PAREIL. L ecart de participation est du meme")
        print("     ordre que l effet cherche : le verdict serait illisible.")
    else:
        print("  Les deux bras jouent. Le controle par bras qui manquait au generateur est")
        print("  RECONSTRUIT sur les donnees deja tombees — la dette est payee sans relancer.")
