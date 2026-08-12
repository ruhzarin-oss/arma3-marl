#!/usr/bin/env python3
"""depouille_bond.py — LE VERDICT DU GESTE N°1 : LE BOND PAR BINOME.

═══ CE QUI A ETE DEPOSE AVANT, ET QU ON NE REECRIT PAS ═══
  GRANDEUR : l ARRIVEE — le premier franchissement du rayon de tenue, journalise par `HMT|G|ARR`.
    Verifie sur pieces le 09/08 : la fiche disait « arrivee », mon banc journalisait aussi la
    tenue ; les deux sont dans les journaux, on juge sur celle du DEPOT.
  PORTE : 10 POINTS. C est un LIEU qu on certifie, pas un agent — la porte de l agent est a 5.
    Corrigee le 08/08 apres que Fable eut releve que j appliquais la mauvaise taille.
  LECTURE APPARIEE PAR COULOIR ⟨regle 12⟩ : la ligne de base appartient au lieu ; un agregat
    sans sa decomposition par lieu n est pas une lecture.

═══ LES CONTROLES, LUS AVANT LA GRANDEUR ═══
  · les deux bras ont JOUE LEUR ROLE — bonds reels chez le professeur, ZERO chez le temoin ;
  · pas de fuite de groupes (limite Arma : 144 par camp, degenerescence silencieuse au 235e) ;
  · zero erreur de script ;
  · l aiguille dans la bande 20-80 % pour LES DEUX bras ⟨regle 2⟩ ;
  · bras equilibres, et chaque couloir joue assez de fois pour etre lu.
"""
import re, sys, math
from collections import defaultdict

F = '/mnt/data/harmattan-sandbox/logs/serverBA.out'
lieu = re.compile(r'HMT\|G\|LIEU\|(\d+)\|(\d+)\|(\d+)')
arr  = re.compile(r'HMT\|G\|ARR\|(\d+)\|')
sante = re.compile(r'HMT\|G\|SANTE\|(\d+)\|(\d+)\|(\d+)')
bond = re.compile(r'HMT\|G\|BOND\|(\d+)\|')

bras, couloir, arrives, bonds = {}, {}, set(), defaultdict(int)
grp = []
err = 0
for L in open(F, encoding='utf-8', errors='ignore'):
    if re.search(r'(?i)script error|Error in expression|Undefined variable', L): err += 1
    m = lieu.search(L)
    if m:
        i = int(m.group(1)); couloir[i] = int(m.group(2)); bras[i] = int(m.group(3)); continue
    m = arr.search(L)
    if m: arrives.add(int(m.group(1))); continue
    m = bond.search(L)
    if m: bonds[int(m.group(1))] += 1; continue
    m = sante.search(L)
    if m: grp.append((int(m.group(2)), int(m.group(3))))

clos = sorted(bras)
if clos: clos = clos[:-1]                      # le dernier accrochage est encore ouvert
P = [i for i in clos if bras[i] == 1]
T = [i for i in clos if bras[i] == 0]
print(f"\n  {len(clos)} accrochages clos · {len(P)} professeur · {len(T)} temoin")

print("\n  CONTROLES — lus AVANT la grandeur")
ok = True
def dire(nom, cond, detail):
    global ok
    print(f"    {'PASSE' if cond else 'TOMBE':>6}  {nom:<40} {detail}")
    if not cond: ok = False

dire("le professeur a REELLEMENT bondi", all(bonds.get(i,0) > 0 for i in P),
     f"{sum(1 for i in P if bonds.get(i,0)>0)} sur {len(P)}")
dire("nul — aucun bond chez le temoin", all(bonds.get(i,0) == 0 for i in T),
     f"{sum(1 for i in T if bonds.get(i,0)>0)} accrochages fautifs sur {len(T)}")
dire("pas de fuite de groupes", (max(max(a,b) for a,b in grp[-50:]) < 100) if grp else False,
     f"pire releve recent : {max(max(a,b) for a,b in grp[-50:]) if grp else -1} (limite 144)")
dire("zero erreur de script", err == 0, f"{err} erreurs")
dire("bras equilibres", min(len(P), len(T)) / max(1, max(len(P), len(T))) > 0.85,
     f"{len(P)} contre {len(T)}")

# ── L AIGUILLE ⟨regle 2⟩ : les deux bras doivent etre dans la bande 20-80 %
tx = {}
for b, nom, ids in ((1, 'professeur', P), (0, 'temoin', T)):
    tx[b] = 100.0 * sum(1 for i in ids if i in arrives) / max(1, len(ids))
dire("aiguille dans la bande 20-80 %", all(20 <= v <= 80 for v in tx.values()),
     f"professeur {tx[1]:.1f} % · temoin {tx[0]:.1f} %")

cols = sorted(set(couloir[i] for i in clos))
assez = [c for c in cols if sum(1 for i in P if couloir[i]==c) >= 20
                         and sum(1 for i in T if couloir[i]==c) >= 20]
dire("chaque couloir joue assez de fois", len(assez) >= 5,
     f"{len(assez)} couloirs sur {len(cols)} avec >= 20 accrochages par bras")

if not ok:
    print("\n  AUCUN VERDICT. Un controle est tombe — le banc ne mesure pas ce qu il pretend.")
    sys.exit(0)

# ── LA GRANDEUR, APPARIEE PAR COULOIR
print(f"\n  LA GRANDEUR — taux d ARRIVEE, couloir par couloir ⟨regle 12⟩")
print(f"    {'couloir':<9}{'prof n':>8}{'prof %':>9}{'tem n':>8}{'tem %':>9}{'ecart':>9}")
ecarts = []
for c in cols:
    ip = [i for i in P if couloir[i]==c]; it = [i for i in T if couloir[i]==c]
    if len(ip) < 20 or len(it) < 20: continue
    ap = 100.0*sum(1 for i in ip if i in arrives)/len(ip)
    at = 100.0*sum(1 for i in it if i in arrives)/len(it)
    ecarts.append(ap - at)
    print(f"    {c:<9}{len(ip):>8}{ap:>8.1f}%{len(it):>8}{at:>8.1f}%{ap-at:>+8.1f}")

def moy(v): return sum(v)/len(v)
def ec(v):
    m=moy(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1)) if len(v)>1 else 0.0
m, s = moy(ecarts), ec(ecarts)
se = s/math.sqrt(len(ecarts))
tc = {2:12.71,3:4.30,4:3.18,5:2.78,6:2.57,7:2.45,8:2.36}.get(len(ecarts), 2.26)
lo, hi = m - tc*se, m + tc*se
sur = sum(1 for e in ecarts if e > 0)

print(f"\n    ecart moyen apparie : {m:+.1f} points   intervalle 95 % [{lo:+.1f} ; {hi:+.1f}]")
print(f"    couloirs ou le professeur gagne : {sur} sur {len(ecarts)}"
      + (f"   (un sur {2**len(ecarts)} par hasard)" if sur == len(ecarts) else ""))

print(f"\n  LA PORTE : 10 POINTS, deposee avant.")
if lo >= 10:
    print(f"    FRANCHIE. Le bond par binome bat la progression simultanee de plus de 10 points")
    print(f"    d arrivee, sur {len(ecarts)} couloirs certifies. Le geste devient PROFESSEUR :")
    print(f"    l eleve peut l imiter, puis doit le battre sur les couloirs tenus a l ecart.")
elif hi <= 0:
    print(f"    RENVERSEE. Le temoin fait MIEUX que le professeur. Le geste sort du repertoire,")
    print(f"    et on le dit — un geste dont le professeur ne bat pas son temoin ne s enseigne pas.")
elif lo > 0:
    print(f"    NON FRANCHIE, mais l effet EXISTE ({m:+.1f} points, intervalle excluant zero).")
    print(f"    Sous 10 points, le lieu ferait un tribunal faible : on ne certifie pas.")
else:
    print(f"    NON FRANCHIE. L intervalle contient zero : rien ne separe les deux bras.")
    print(f"    Le geste ne s enseigne pas, et c est un resultat, pas un echec.")
