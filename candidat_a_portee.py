#!/usr/bin/env python3
"""LE PIEGE DU CONTROLE POSITIF : une colonne inerte peut l etre pour DEUX raisons.

  (a) la politique l IGNORE ;
  (b) elle ne VARIE PAS — et alors la permuter est l identite, l instrument n a rien fait.

(b) est la meme faute que la pente jugee sur un seuil : croire qu on a mesure parce qu on a
un nombre. On tranche avec deux grandeurs qui ne se confondent pas :

  · DISPERSION  : ecart-type de la colonne entre environnements. Si ~0, permuter = ne rien faire.
  · DECISIONS CHANGEES : part des actions dont l argmax bascule quand on permute. C est la
    mesure DIRECTE que le changement d entree a atteint la sortie.

Une colonne qui varie ET dont la permutation ne change aucune decision est REELLEMENT ignoree.
Une colonne qui change des decisions sans changer la prise dit autre chose : elle est lue,
mais ce qu elle change ne sert a rien.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger, COLS

NOMS = ["apx", "apy", "dgx", "dgy", "alive", "SLOPE", "dcover", "los", "nd"]
pol = charger("cpu"); DEV = next(pol.parameters()).device
e = B.monde(256, B.GRAINES_TEST[0])
o = e.reset()

disp = [0.0] * 9; chg = [0.0] * 9; n_pas = 0
for t in range(60):
    x = o.clone().to(DEV)
    with torch.no_grad():
        base = pol(x)[0].argmax(-1)
    for c in range(9):
        y = x.clone()
        y[:, :, c] = y[torch.randperm(y.shape[0], device=DEV), :, c]
        with torch.no_grad():
            a2 = pol(y)[0].argmax(-1)
        chg[c] += float((a2 != base).float().mean())
        disp[c] += float(x[:, :, c].std())
    n_pas += 1
    o, _, done, _ = e.step(base.to(o.device), auto_reset=False)
    if bool(done.all()): break

print("\n  %-8s %14s %22s" % ("colonne", "dispersion", "decisions changees"))
for c in range(9):
    m = "  ⬅ la pente" if c == 5 else ""
    print("  %-8s %13.3f %20.1f %%%s" % (NOMS[c], disp[c]/n_pas, 100*chg[c]/n_pas, m))
print("\n  (%d pas joues)" % n_pas)
