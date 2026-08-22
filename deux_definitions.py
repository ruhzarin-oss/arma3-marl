#!/usr/bin/env python3
"""LES DEUX MONDES NE COMPTENT PAS LE MEME SUCCES — combien ca coute ?

  GYMNASE  `pris |= neuf` (boucle.py:123) — CUMULE. Une fois passe sous 25 m, acquis.
           « est-elle DEJA ARRIVEE ? »
  ARMA     `prise=(lig[-1][2] < 25)` (lire_natif.py:36) — DERNIERE LIGNE seulement, et
           `_dmin` est reinitialise a 1e9 a chaque etat. « Y EST-ELLE A LA FIN ? »

On rejoue les deux nuits sous la regle du GYMNASE, sans rien changer d autre : meme
lecteur depose pour la selection des episodes, meme seuil de 25 m.

⚠️ BORNE INFERIEURE. Le journal n imprime qu un pas sur cinq (plus la ligne de fin) : un
passage sous 25 m entre deux impressions est INVISIBLE. Le « deja arrive » mesure ici est
donc SOUS-ESTIME — l ecart reel entre les deux regles est au moins celui-la.
"""
import re, glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

RE_L = re.compile(r'^\s+(\d+)\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', re.M)

def trace(f):
    t = open(f, errors="ignore").read()
    lg = [(int(p), int(v), int(dd), int(d)) for p, v, dd, d in RE_L.findall(t)]
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(-?\d+)', t)
    if fin: lg.append((int(fin.group(1)), int(fin.group(2)), -1, int(fin.group(3))))
    return lg

print("\n  %-11s %14s %16s %10s %12s" % ("nuit", "regle ARMA", "regle GYMNASE", "gain", "n"))
tab = {}
for nom, dos in [("NATIF", "/mnt/data/natif"), ("POLITIQUE", "/mnt/data/politique")]:
    fin_ok = 0; deja = 0; n = 0; conv = 0
    for f in sorted(glob.glob("%s/p*_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok": continue
        lg = trace(f)
        if len(lg) < 2: continue
        n += 1
        a = bool(e["prise"])                                   # regle ARMA, telle que deposee
        g = any(v > 0 and 0 <= d < 25 for _, v, _, d in lg)     # regle GYMNASE : deja arrive
        fin_ok += a; deja += g; conv += (g and not a)
    tab[nom] = (100.0*fin_ok/n, 100.0*deja/n, n, conv)
    print("  %-11s %12.1f %% %14.1f %% %9.1f %12d" % (nom, tab[nom][0], tab[nom][1],
                                                       tab[nom][1]-tab[nom][0], n))
print("\n  episodes qui ARRIVENT puis REPARTENT (echec sous la regle d Arma,")
print("  succes sous celle du gymnase) :")
for nom in tab: print("    %-11s %d" % (nom, tab[nom][3]))
print("\n  ecart NATIF - POLITIQUE")
print("    regle ARMA (deposee) : %+.1f points" % (tab["NATIF"][0] - tab["POLITIQUE"][0]))
print("    regle GYMNASE        : %+.1f points" % (tab["NATIF"][1] - tab["POLITIQUE"][1]))
