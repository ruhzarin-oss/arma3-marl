#!/usr/bin/env python3
"""calibrage.py — UN SEUL BALAYAGE, DEUX CALIBRATIONS.

⟨Fable, 10/08⟩ « Sépare le TIRAGE de la LECTURE. Le balayage qui tourne est l instrument ; la
calibration est une lecture de bande sur une GRANDEUR NOMMEE. Un seul balayage peut donc servir
aux deux — memes mondes, memes tirages — mais il rendra DEUX calibrations : chaque geste lit sa
bande sur sa grandeur et choisit SON point de fonctionnement sur l axe balaye. S ils tombent sur
le meme effectif defenseur, un monde servira deux bancs ; s ils divergent, deux mondes. »

⚠️ ET LES PERTES ETAIENT DEJA AU JOURNAL. La ligne de fin porte les survivants de chaque camp,
la ligne de debut porte l effectif attaquant. Aucun ajout de journalisation n a ete necessaire —
donc RIEN N A CHANGE dans le monde pendant le balayage, et l aveugle est intact.

CE QUE CE SCRIPT LIT, ET RIEN D AUTRE : pour chaque effectif defenseur balaye, le taux de prise
(grandeur du geste n°2) et le taux de survie (grandeur du geste n°3). Il ne compare aucun bras —
le balayage n en a qu un — et ne rend aucun verdict.

LA BANDE : 20 a 80 % ⟨regle 2, l aiguille au butoir⟩. Le point de fonctionnement retenu est
celui qui tombe au plus pres du MILIEU de la bande, la ou l instrument a le plus de course.
"""
import re, sys
from collections import defaultdict
from cles import Segmenteur

F = sys.argv[1:] or ['/mnt/data/harmattan-sandbox/logs/serverA2.out']
deb = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|(\d+)\|')
fin = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|\d+\|(\w+)\|(\d+)\|(-?\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)\|')

D, R = {}, {}
# ⚠️ CLE = (fichier, segment, id). Les identifiants d accrochage REPARTENT A 1 a chaque
# redemarrage de serveur : sans segmentation, deux journaux mis bout a bout fusionnent
# silencieusement des accrochages DIFFERENTS portant le meme numero — un cumul naif rendait
# 9575 accrochages la ou l archive en portait 3986. Le segment s incremente quand un id RECULE.
_seg = Segmenteur()


def _lignes(src):
    for _f in (src if isinstance(src, (list, tuple)) else [src]):
        for _L in open(_f, encoding='utf-8', errors='ignore'):
            yield _f, _L


_f = None
for _f, L in _lignes(F):
    m = deb.search(L)
    if m:
        D[_seg.cle(_f, int(m.group(1)))] = (int(m.group(2)), int(m.group(3)), int(m.group(4)))  # campDef, nDef, nAtt
        continue
    m = fin.search(L)
    if m:
        R[_seg.cle_passive(_f, int(m.group(1)))] = (int(m.group(5)), int(m.group(6)), int(m.group(7)))  # pris, viv_e, viv_o

clos = sorted(set(D) & set(R), key=str)
print(f"\n  {len(clos)} accrochages clos · balayage de l effectif defenseur")
if not clos:
    print("  rien a lire encore"); sys.exit(0)

g = defaultdict(lambda: {'n': 0, 'pris': 0, 'perdus': 0, 'engages': 0})
for i in clos:
    campDef, nDef, nAtt = D[i]
    pris, ve, vo = R[i]
    # camp 0 = east, camp 1 = west ⟨lu dans le code : si east est efface, le vainqueur est 1⟩
    survivants = vo if campDef == 0 else ve
    c = g[nDef]
    c['n'] += 1; c['pris'] += pris
    c['perdus'] += max(0, nAtt - survivants); c['engages'] += nAtt

# ⚠️ TROIS ETATS, PAS DEUX. Le premier jet n en rendait que deux — « dans la bande » ou
# « aucun reglage dans la bande » — et affichait donc un VERDICT FAUX quand la verite etait
# « je ne sais pas encore » : a 12 accrochages sur onze reglages, il annoncait qu aucun ne
# convenait. ⟨Fable, 10/08 : « un instrument qui affiche 'aucun reglage dans la bande' quand la
# verite est 'je ne sais pas encore' rend un verdict faux ; c est exactement la panne
# silencieuse que le faux journal existe pour attraper »⟩
MINI = 12          # accrochages minimum pour qu un reglage ait le droit d etre lu
print(f"\n  {'defenseurs':<12}{'n':>5}{'PRISE':>9}{'SURVIE':>10}    etat")
print("  " + "-" * 62)
best = {}; muets = 0
for nd in sorted(g):
    c = g[nd]
    if c['n'] < MINI:
        muets += 1
        print(f"  {nd:<12}{c['n']:>5}{'·':>9}{'·':>10}    ─ pas assez ({c['n']}/{MINI})")
        continue
    pr = 100.0 * c['pris'] / c['n']
    su = 100.0 * (c['engages'] - c['perdus']) / max(1, c['engages'])
    b2 = 20 <= pr <= 80
    b3 = 20 <= su <= 80
    marque = ('  n°2' if b2 else '') + ('  n°3' if b3 else '')
    print(f"  {nd:<12}{c['n']:>5}{pr:>8.0f}%{su:>9.0f}%{marque if marque else '    hors bande'}")
    if b2: best.setdefault('n2', []).append((abs(pr - 50), nd, pr))
    if b3: best.setdefault('n3', []).append((abs(su - 50), nd, su))
print("  " + "-" * 62)
lus = len([nd for nd in g if g[nd]['n'] >= MINI])
print(f"  {lus} reglages lisibles · {muets} encore muets")

print("\n  LE POINT DE FONCTIONNEMENT — au plus pres du milieu de bande, ou l instrument a le")
print("  plus de course. Chaque geste choisit LE SIEN sur sa propre grandeur.")
for k, nom, gr in (('n2', 'geste n°2 (appui-feu)', 'prise'), ('n3', 'geste n°3 (couvert)', 'survie')):
    if k in best:
        d, nd, v = sorted(best[k])[0]
        print(f"    {nom:<26} -> {nd} defenseurs   ({gr} {v:.0f} %)")
    elif lus == 0:
        print(f"    {nom:<26} -> ON NE SAIT PAS ENCORE. Aucun reglage n a atteint {MINI}")
        print(f"       {'':<26}    accrochages. Ce n est PAS un resultat — c est un compteur.")
    else:
        print(f"    {nom:<26} -> aucun des {lus} reglages lisibles n est dans la bande.")
        print(f"       {'':<26}    Passer a l axe suivant ⟨ordre depose : distance, puis")
        print(f"       {'':<26}    competence, puis armement⟩.")

if lus == 0:
    print("\n  ⚠️ RIEN N EST LISIBLE. Le balayage continue ; revenir quand les reglages auront")
    print("     leurs douze accrochages. Ne lire aucune conclusion de cet ecran.")
elif 'n2' in best and 'n3' in best and sorted(best['n2'])[0][1] == sorted(best['n3'])[0][1]:
    print("\n  Les deux gestes tombent sur le MEME effectif : un seul monde servira deux bancs.")
elif 'n2' in best and 'n3' in best:
    print("\n  Les deux gestes divergent : DEUX mondes, et c est le prix normal ⟨Fable⟩ —")
    print("  on ne paie simplement pas les tirages deux fois.")
