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
from cles import Segmenteur, corpus_sain, empreinte_par_canal
from collections import defaultdict

# ⚠️ SECONDE LECTURE : plusieurs journaux, et le SEGMENTEUR. Les identifiants d accrochage
# repartent a 1 a chaque redemarrage ; sans lui, deux fichiers bout a bout fusionneraient des
# accrochages differents portant le meme numero.
F = sys.argv[1:] or ['/mnt/data/harmattan-sandbox/logs/serverBA.out']
# ⚠️ LE CORPUS SE DECLARE, IL NE SE RAMASSE PAS. Un glob `serverBA*` a ramasse une
# vingtaine de journaux etrangers ET le meme journal deux fois. On refuse les doublons ici,
# bruyamment, avant de lire quoi que ce soit.
F, _dbl = corpus_sain(F)
for _a, _b in _dbl:
    print(f"  ⚠️ DOUBLON PARFAIT ecarte : {_a}  ==  {_b}")
_jum = empreinte_par_canal(F)
for _sig, _v in _jum.items():
    print(f"  ⚠️ MEMES COMPTES PAR CANAL {_sig} : {[__import__('os').path.basename(x) for x in _v]}")
    print( "     -> meme campagne sous deux noms. On ne lit pas un corpus ambigu.")
    raise SystemExit(1)
print(f"  corpus : {len(F)} journal(aux) retenu(s)")
_seg = Segmenteur()


def _lignes(src):
    for _f in src:
        for _L in open(_f, encoding='utf-8', errors='ignore'):
            yield _f, _L
lieu = re.compile(r'HMT\|G\|LIEU\|(\d+)\|(\d+)\|(\d+)')
arr  = re.compile(r'HMT\|G\|ARR\|(\d+)\|')
sante = re.compile(r'HMT\|G\|SANTE\|(\d+)\|(\d+)\|(\d+)')
bond = re.compile(r'HMT\|G\|BOND\|(\d+)\|')

bras, couloir, arrives, bonds = {}, {}, set(), defaultdict(int)
grp = []
err = 0
for _f, L in _lignes(F):
    if re.search(r'(?i)script error|Error in expression|Undefined variable', L): err += 1
    m = lieu.search(L)
    if m:
        # ⚠️ LA LIGNE `LIEU` EST LE FLUX MAITRE : une par accrochage, en ordre croissant.
        # C est elle qui fait avancer le segment ; tous les autres canaux le SUIVENT.
        # Faute payee a l instant : j avais mis les bonds sous une cle (fichier, segment, id)
        # et les couloirs sous un simple entier — ils ne pouvaient plus se rencontrer, et le
        # controle « le professeur a reellement bondi » rendait 0 sur 1991 alors que le journal
        # porte 54 563 lignes de bond. Le controle a attrape MA faute, pas celle du monde.
        i = _seg.cle(_f, int(m.group(1)))
        couloir[i] = int(m.group(2)); bras[i] = int(m.group(3)); continue
    m = arr.search(L)
    if m: arrives.add(_seg.cle_passive(_f, int(m.group(1)))); continue
    m = bond.search(L)
    if m: bonds[_seg.cle_passive(_f, int(m.group(1)))] += 1; continue
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
# ⚠️ NIVEAU 99 %, PAS 95. C est le PEAGE DE LA SECONDE VUE, depose avant lancement :
# « j ai regarde une fois, et une seconde lecture non tarifee gonfle la probabilite de passage
# sous le nul — c est l arret optionnel par la porte de derriere. » Le seuil de 10 points, lui,
# ne bouge pas d un cheveu. ⟨PROTOCOLE_BOND_SECONDE_LECTURE.md⟩
tc = {2:63.66,3:9.92,4:5.84,5:4.60,6:4.03,7:3.71,8:3.50}.get(len(ecarts), 3.36)
lo, hi = m - tc*se, m + tc*se
sur = sum(1 for e in ecarts if e > 0)

print(f"\n    ecart moyen apparie : {m:+.1f} points   intervalle 99 % [{lo:+.1f} ; {hi:+.1f}]")
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
