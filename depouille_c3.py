#!/usr/bin/env python3
"""depouille_c3 — LE VERDICT DU GESTE N°3 : LA PRISE DE COUVERT SOUS LE FEU.

═══ CE QUI A ETE DEPOSE AVANT, ET QU ON NE REECRIT PAS ═══
  PROFESSEUR : l equipe se jette a couvert au premier tir proche, se couche, repart apres 10 s.
  TEMOIN     : elle continue debout, meme axe, meme lieu, meme effectif.
  GRANDEUR   : LES PERTES — la survie de l equipe a la traversee.
  PORTE      : 10 POINTS, lue SUR LA BORNE ⟨regle 14⟩.
  APPARIEMENT: par LIEU ⟨regle 12⟩ — un agregat sans sa decomposition par lieu n est pas une
               lecture. Le canal `LIEUC3` porte le lieu de chaque accrochage.

⚠️ LE CORPUS EST DECLARE, PAS RAMASSE. Seuls comptent les accrochages joues APRES les deux
corrections du geste : (1) `FiredNear` se declenche pour les hommes proches du TIREUR, donc le
professeur se couchait au feu de son propre binome — 121 declenchements sur 130 a distance
ZERO ; (2) le drapeau « sous le feu » durait 2 s pour un echantillonnage a 2 s, invisible une
fois sur deux. Tout ce qui precede est ecarte nommement.
"""
import re, sys, math
from collections import defaultdict
from cles import Segmenteur, corpus_sain, empreinte_par_canal

F = sys.argv[1:] or ["/mnt/data/harmattan-sandbox/logs/pause_12-08_soir/serverC3.out"]
F, dbl = corpus_sain(F)
for a, b in dbl:
    print(f"  ⚠️ DOUBLON PARFAIT ecarte : {a} == {b}")
jum = empreinte_par_canal(F, canaux=("LIEUC3", "COUVERT", "C3GESTE", "fin"))
if jum:
    print(f"  ⚠️ MEME CAMPAGNE SOUS DEUX NOMS : {jum} — on ne lit pas un corpus ambigu."); sys.exit(1)
print(f"\n  corpus : {len(F)} journal(aux) declare(s)")

deb = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|(\d+)\|')
fin = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|\d+\|(\w+)\|(\d+)\|(-?\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)\|')
lieu = re.compile(r'HMT\|G\|LIEUC3\|(\d+)\|(-?\d+)\|(-?\d+)')
couv = re.compile(r'HMT\|G\|COUVERT\|(\d+)\|(-?\d+)\|(\d)\|(\d)\|(\d)\|(\d)')
gest = re.compile(r'HMT\|G\|C3GESTE\|(-?\d+)\|(\w+)\|(\d+)(?:\|adverse\|(\d))?')

seg = Segmenteur()
D, R, L, BRAS = {}, {}, {}, {}
couche = defaultdict(int); nsamp = defaultdict(int)
gestes = 0; gestes_adverses = 0; err = 0
for f in F:
    for line in open(f, encoding='utf-8', errors='ignore'):
        if 'Error in expression' in line: err += 1
        m = lieu.search(line)
        if m:
            k = seg.cle(f, int(m.group(1))); L[k] = (int(m.group(2)), int(m.group(3))); continue
        m = deb.search(line)
        if m:
            D[seg.cle_passive(f, int(m.group(1)))] = dict(campDef=int(m.group(2)), nAtt=int(m.group(4))); continue
        m = fin.search(line)
        if m:
            R[seg.cle_passive(f, int(m.group(1)))] = dict(ve=int(m.group(6)), vo=int(m.group(7)),
                                                          pris=int(m.group(5))); continue
        m = couv.search(line)
        if m:
            k = seg.cle_passive(f, int(m.group(1)))
            BRAS[k] = int(m.group(6)); nsamp[k] += 1
            if m.group(3) == '2': couche[k] += 1
            continue
        m = gest.search(line)
        if m and m.group(2) == 'a_terre':
            gestes += 1
            if m.group(4) == '1': gestes_adverses += 1

clos = [k for k in L if k in D and k in R and k in BRAS]
E = []
for k in clos:
    d, r = D[k], R[k]
    surv = r['vo'] if d['campDef'] == 0 else r['ve']
    E.append(dict(k=k, lieu=L[k], bras=BRAS[k], nAtt=d['nAtt'], pris=r.get('pris', 0),
                  survie=100.0 * surv / max(d['nAtt'], 1), couche=couche.get(k, 0), n=nsamp.get(k, 0)))
P = [e for e in E if e['bras'] == 1]; T = [e for e in E if e['bras'] == 0]
print(f"  {len(E)} accrochages clos · {len(P)} professeur · {len(T)} temoin")

print("\n  CONTROLES — lus AVANT la grandeur")
ok = True
def dire(nom, cond, detail):
    global ok
    print(f"    {'PASSE' if cond else 'TOMBE':>6}  {nom:<46} {detail}")
    if not cond: ok = False
moy = lambda v: sum(v) / len(v) if v else 0.0

pc = 100.0 * sum(e['couche'] for e in P) / max(sum(e['n'] for e in P), 1)
tc = 100.0 * sum(e['couche'] for e in T) / max(sum(e['n'] for e in T), 1)
dire("BRAS — le professeur se couche PLUS que le temoin", pc > tc + 5,
     f"{pc:.1f} % contre {tc:.1f} % des echantillons")
dire("BRAS — le geste ne repond QU AU FEU ADVERSE", gestes > 0 and gestes_adverses == gestes,
     f"{gestes_adverses} sur {gestes} mises a terre")
dire("zero erreur de script", err == 0, f"{err} erreurs")
dire("bras equilibres", len(P) and len(T) and abs(len(P) - len(T)) / max(len(P), len(T)) < 0.25,
     f"{len(P)} contre {len(T)}")
sp, st = moy([e['survie'] for e in P]), moy([e['survie'] for e in T])
dire("aiguille dans la bande 20-80 % (les deux bras)", 20 <= sp <= 80 and 20 <= st <= 80,
     f"professeur {sp:.1f} % · temoin {st:.1f} %")
lieux = sorted({e['lieu'] for e in E})
assez = [l for l in lieux if sum(1 for e in P if e['lieu'] == l) >= 20
         and sum(1 for e in T if e['lieu'] == l) >= 20]
dire("chaque lieu joue assez de fois", len(assez) >= 2,
     f"{len(assez)} lieux sur {len(lieux)} avec >= 20 accrochages par bras")

# ─── L AIGUILLE, LIEU PAR LIEU ⟨regle 2⟩ ────────────────────────────────────────────────
# ⚠️ UN LIEU CERTIFIE PAR LE GEOMETRE PEUT ETRE INJOUABLE. Mesure du 12/08 : le lieu
# (1850,2750) rend TROIS prises sur quarante-quatre — 7 % — avec trente-cinq accrochages
# finis au chronometre, quand ses voisins sont entre 43 et 59 %. Il a pourtant passe la
# certification geometrique : couvert servi, vues, silhouette, tout y etait.
# La geometrie dit que le lieu EST un couloir ; elle ne dit pas qu on peut y jouer. Un lieu
# dont l aiguille est au butoir ne separe rien, quel que soit son ecart — la regle 2 le dit
# au point de fonctionnement du jugement, et c est ici ce point.
# On les ECARTE, et on les NOMME. Jamais silencieusement.
BANDE = (20.0, 80.0)
au_butoir = []
for l in list(assez):
    pr = 100.0 * sum(1 for e in E if e['lieu'] == l and e.get('pris', 0)) / max(
        sum(1 for e in E if e['lieu'] == l), 1)
    if not (BANDE[0] <= pr <= BANDE[1]):
        au_butoir.append((l, pr)); assez.remove(l)
for l, pr in au_butoir:
    print(f"    {'ECARTE':>6}  lieu {str(l):<16} aiguille au butoir : {pr:.0f} % de prise")
dire("aiguille dans la bande 20-80 %, LIEU PAR LIEU", not au_butoir,
     f"{len(au_butoir)} lieu(x) ecarte(s) · {len(assez)} retenu(s)")
dire("assez de lieux RETENUS pour apparier", len(assez) >= 2,
     f"{len(assez)} lieux dans la bande avec l effectif requis")

if not ok:
    print("\n  AUCUN VERDICT. Un controle est tombe — le banc ne mesure pas ce qu il pretend.")
    sys.exit(0)

print("\n  LA GRANDEUR — SURVIE de l equipe, lieu par lieu ⟨regle 12⟩")
print(f"    {'lieu':<16}{'prof n':>8}{'prof %':>9}{'tem n':>8}{'tem %':>9}{'ecart':>9}")
ecarts = []
for l in assez:
    a = [e['survie'] for e in P if e['lieu'] == l]; b = [e['survie'] for e in T if e['lieu'] == l]
    ec = moy(a) - moy(b); ecarts.append(ec)
    print(f"    {str(l):<16}{len(a):>8}{moy(a):>8.1f}%{len(b):>8}{moy(b):>8.1f}%{ec:>+9.1f}")
m = moy(ecarts)
s = math.sqrt(sum((x - m) ** 2 for x in ecarts) / (len(ecarts) - 1)) if len(ecarts) > 1 else 0.0
se = s / math.sqrt(len(ecarts))
tv = {2:12.71,3:4.30,4:3.18,5:2.78,6:2.57,7:2.45,8:2.36}.get(len(ecarts), 2.26)
lo, hi = m - tv * se, m + tv * se
print(f"\n    ecart moyen apparie : {m:+.1f} points   intervalle 95 % [{lo:+.1f} ; {hi:+.1f}]")
print(f"    lieux ou le professeur gagne : {sum(1 for e in ecarts if e > 0)} sur {len(ecarts)}")
print(f"\n  LA PORTE : 10 POINTS, deposee avant, lue SUR LA BORNE.")
if lo >= 10:
    print("    FRANCHIE. Se jeter a couvert sous le feu bat la traversee debout de plus de")
    print("    10 points de survie. Le geste devient PROFESSEUR.")
elif hi <= 0:
    print("    RENVERSEE. Le temoin survit MIEUX. Le geste sort du repertoire, et on le dit.")
elif lo > 0:
    print(f"    NON FRANCHIE, mais l effet EXISTE ({m:+.1f} points, intervalle excluant zero).")
else:
    print("    NON FRANCHIE. L intervalle contient zero : rien ne separe les deux bras.")
