#!/usr/bin/env python3
"""CONTROLE POSITIF DU BROUILLEUR — regle 16. Ecrit APRES A1/A2 verts, joue AVANT le depot.

Le candidat A rend 0,7 point d ecart. Deux lectures possibles, et une seule est vraie :
  (a) la politique est aveugle a la pente ;
  (b) MON BROUILLEUR NE BROUILLE RIEN, et il rendrait 0,7 point sur n importe quelle colonne.

On tranche en permutant, avec le MEME code, des colonnes dont la politique ne peut pas se
passer. Si celles-la s effondrent et la pente non, le brouilleur mord et (a) tient.
Si tout reste plat, l instrument est muet et le candidat A ne conclut RIEN.

⭐ Cliquet : un instrument qui parle sans mesurer ment dans les DEUX sens.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger, COLS

NOMS = {0: "apx  (ma position x)", 1: "apy  (ma position y)", 2: "dgx  (cap vers le but x)",
        3: "dgy  (cap vers le but y)", 4: "alive (je suis vivant)", 5: "SLOPE (la pente)",
        6: "dcover (distance au bati)", 7: "los  (je suis vu)", 8: "nd   (defenseur le plus proche)"}
GRAINES = B.GRAINES_TEST[:3]
pol = charger("cpu"); DEV = next(pol.parameters()).device

def faire(col):
    def choisir(o, t):
        x = o.clone().to(DEV)
        if col is not None:
            n = x.shape[0]
            x[:, :, col] = x[torch.randperm(n, device=DEV), :, col]
        with torch.no_grad():
            lo, _ = pol(x if x.shape[-1] == len(COLS) else x[:, :, COLS])
        return lo.argmax(-1).to(o.device), None, None
    return choisir

def taux(col):
    v = []
    for g in GRAINES:
        s, *_ = B.jouer(B.monde(256, g), faire(col))
        v.append(s["prise"])
    return sum(v) / len(v)

ref = taux(None)
print("\n  temoin, observation INTACTE : %.1f %%\n" % ref)
print("  %-32s %10s %10s" % ("colonne permutee", "prise", "chute"))
res = {}
for c in sorted(NOMS):
    t = taux(c); res[c] = ref - t
    marque = "  ⬅ la pente" if c == 5 else ""
    print("  %-32s %8.1f %% %9.1f%s" % (NOMS[c], t, ref - t, marque))
autres = [res[c] for c in res if c != 5]
print("\n  chute sur la PENTE          : %5.1f point" % res[5])
print("  chute MAXIMALE ailleurs     : %5.1f points  (colonne %d)" %
      (max(autres), max(res, key=lambda c: -1e9 if c == 5 else res[c])))
mord = max(autres) >= 5.0
print("\n  Le brouilleur MORD (>= 5 pts sur au moins une colonne) : %s" % ("OUI" if mord else "NON"))
if mord and res[5] < 3.0:
    print("  ➤ CONTROLE POSITIF PASSE. Le meme code effondre d autres colonnes et laisse")
    print("    la pente intacte : la politique est REELLEMENT aveugle a la pente.")
elif not mord:
    print("  ⛔ INSTRUMENT MUET. Aucune colonne ne bouge — le brouilleur ne brouille rien.")
    print("    Le candidat A ne conclut RIEN et son resultat ne se cite pas.")
else:
    print("  ⛔ La pente chute autant que le reste : relire A1/A2.")
