#!/usr/bin/env python3
"""depouille_appui_lieu.py — LE VERDICT DU GESTE N°2 : LA PORTE 0 DU LIEU.

═══ CE QUI A ETE DEPOSE AVANT ⟨CRITERES_GESTE2_APPUI.md, 08/08⟩ ═══
  PROFESSEUR : 3 hommes en appui au poste certifie + 5 a l assaut.
  TEMOIN     : 8 hommes tous a l assaut, meme axe, meme lieu. Effectif TOTAL identique.
  GRANDEUR   : LA PRISE — le champ `_pris` du journal de fin.
  PORTE      : 10 POINTS. C est un LIEU qu on certifie, pas un agent.
  LECTURE    : SUR LA BORNE ⟨regle 14, deposee le 10/08 : une porte muette sur sa lecture se
               lit sur la borne, CONTRE le demandeur du certificat ; et l audit des portes deja
               deposees a porte cette note sur celle-ci⟩.
  LECTURE APPARIEE PAR LIEU ⟨regle 12⟩ : la ligne de base appartient au lieu.

═══ CE QUI EST DEJA ACQUIS ET NE SE REJOUE PAS ICI ═══
  L ETAGE 1 (mecanique) a rendu VIVANT le 09/08 : moyenne geometrique 0,549 — 45 % de capacite
  en moins — intervalle [0,343 ; 0,878], six terrains sur six. Il est EN SURSIS (deux sessions
  sur trois). Ce banc-ci ne le rejuge pas : il demande si l appui fait PRENDRE L OBJECTIF.
"""
import re, sys, math
from collections import defaultdict

F = '/mnt/data/harmattan-sandbox/logs/serverA2.out'
lieu = re.compile(r'HMT\|G\|LIEUAP\|(\d+)\|(\d+)\|(\d+)')
fin  = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|\d+\|(\w+)\|(\d+)\|(-?\d+)\|(\d+)')
sante = re.compile(r'HMT\|G\|SANTE\|(\d+)\|(\d+)\|(\d+)')
appui = re.compile(r'HMT\|G\|APPUI\|(\d+)\|(\w+)\|')

bras, couloir, pris, ouvre, leve = {}, {}, {}, set(), set()
grp, err = [], 0
for L in open(F, encoding='utf-8', errors='ignore'):
    if re.search(r'(?i)script error|Error in expression|Undefined variable', L): err += 1
    m = lieu.search(L)
    if m:
        i = int(m.group(1)); couloir[i] = int(m.group(2)); bras[i] = int(m.group(3)); continue
    m = fin.search(L)
    if m: pris[int(m.group(1))] = int(m.group(5)); continue
    m = appui.search(L)
    if m:
        (ouvre if m.group(2) == 'ouvre' else leve).add(int(m.group(1))); continue
    m = sante.search(L)
    if m: grp.append((int(m.group(2)), int(m.group(3))))

clos = sorted(i for i in bras if i in pris)
P = [i for i in clos if bras[i] == 1]
T = [i for i in clos if bras[i] == 0]
print(f"\n  {len(clos)} accrochages clos · {len(P)} professeur · {len(T)} temoin")

print("\n  CONTROLES — lus AVANT la grandeur")
ok = True
def dire(nom, cond, detail):
    global ok
    print(f"    {'PASSE' if cond else 'TOMBE':>6}  {nom:<42} {detail}")
    if not cond: ok = False

dire("l appui a REELLEMENT ouvert le feu", all(i in ouvre for i in P),
     f"{sum(1 for i in P if i in ouvre)} sur {len(P)}")
dire("nul — aucun appui chez le temoin", all(i not in ouvre for i in T),
     f"{sum(1 for i in T if i in ouvre)} accrochages fautifs sur {len(T)}")
dire("pas de fuite de groupes", (max(max(a,b) for a,b in grp[-50:]) < 100) if grp else False,
     f"pire releve recent : {max(max(a,b) for a,b in grp[-50:]) if grp else -1} (limite 144)")
dire("zero erreur de script", err == 0, f"{err} erreurs")
dire("bras equilibres", min(len(P), len(T)) / max(1, max(len(P), len(T))) > 0.85,
     f"{len(P)} contre {len(T)}")

tx = {b: 100.0*sum(1 for i in ids if pris[i] == 1)/max(1, len(ids))
      for b, ids in ((1, P), (0, T))}
dire("aiguille dans la bande 20-80 %", all(20 <= v <= 80 for v in tx.values()),
     f"professeur {tx[1]:.1f} % · temoin {tx[0]:.1f} %")

cols = sorted(set(couloir[i] for i in clos))
assez = [c for c in cols if sum(1 for i in P if couloir[i]==c) >= 20
                         and sum(1 for i in T if couloir[i]==c) >= 20]
dire("chaque lieu joue assez de fois", len(assez) >= 5,
     f"{len(assez)} lieux sur {len(cols)} avec >= 20 accrochages par bras")

if not ok:
    print("\n  AUCUN VERDICT. Un controle est tombe — le banc ne mesure pas ce qu il pretend.")
    sys.exit(0)

print(f"\n  LA GRANDEUR — taux de PRISE, lieu par lieu ⟨regle 12⟩")
print(f"    {'lieu':<7}{'prof n':>8}{'prof %':>9}{'tem n':>8}{'tem %':>9}{'ecart':>9}")
ecarts = []
for c in cols:
    ip = [i for i in P if couloir[i]==c]; it = [i for i in T if couloir[i]==c]
    if len(ip) < 20 or len(it) < 20: continue
    ap = 100.0*sum(1 for i in ip if pris[i]==1)/len(ip)
    at = 100.0*sum(1 for i in it if pris[i]==1)/len(it)
    ecarts.append(ap - at)
    print(f"    {c:<7}{len(ip):>8}{ap:>8.1f}%{len(it):>8}{at:>8.1f}%{ap-at:>+8.1f}")

def moy(v): return sum(v)/len(v)
def ec(v):
    m=moy(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1)) if len(v)>1 else 0.0
m, s = moy(ecarts), ec(ecarts)
se = s/math.sqrt(len(ecarts))
tc = {2:12.71,3:4.30,4:3.18,5:2.78,6:2.57,7:2.45,8:2.36}.get(len(ecarts), 2.26)
lo, hi = m - tc*se, m + tc*se
sur = sum(1 for e in ecarts if e > 0)

print(f"\n    ecart moyen apparie : {m:+.1f} points   intervalle 95 % [{lo:+.1f} ; {hi:+.1f}]")
print(f"    lieux ou le professeur gagne : {sur} sur {len(ecarts)}"
      + (f"   (un sur {2**len(ecarts)} par hasard)" if sur == len(ecarts) else ""))

print(f"\n  LA PORTE : 10 POINTS sur la PRISE, lue sur la BORNE ⟨regle 14⟩")
if lo >= 10:
    print(f"    FRANCHIE. L appui-feu fait PRENDRE l objectif de plus de 10 points, sur")
    print(f"    {len(ecarts)} lieux certifies. Le geste n°2 devient PROFESSEUR.")
elif hi <= 0:
    print(f"    RENVERSEE. Le temoin prend PLUS souvent que le professeur. Le geste sort du")
    print(f"    repertoire — un professeur qui ne bat pas son temoin ne s enseigne pas.")
elif lo > 0:
    print(f"    NON FRANCHIE, mais l effet EXISTE ({m:+.1f} points, intervalle excluant zero).")
    print(f"    Sous 10 points, on ne certifie pas — la campagne est a dimensionner.")
else:
    print(f"    NON FRANCHIE. L intervalle contient zero : rien ne separe les deux bras.")
    print(f"    L appui supprime (etage 1 : -45 % de capacite) mais ne fait pas PRENDRE.")
    print(f"    C est un resultat, et il vaut d etre dit : la mecanique ne suffit pas.")
