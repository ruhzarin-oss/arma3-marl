#!/usr/bin/env python3
"""LES DOUZE COLONNES, CETTE FOIS — l ablation du 22/08 n en avait teste que NEUF.

La politique lit 12 entrees : les 9 de base + 3 de POSTURE. Le controle positif deposé
(`VERDICT_CANDIDAT_A_22-08.md`) a brouille les 9 premieres et conclu « elle ne lit que sa
position et son cap ». Il ne pouvait pas le conclure : les 3 dernieres n avaient jamais
ete brouillees. Une conclusion qui porte sur 12 colonnes ne se tire pas sur 9.

Meme brouilleur, memes graines, meme temoin. On ajoute les 3 manquantes, et deux bras
groupes qui repondent a la question directement.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

NOMS = ["apx", "apy", "dgx", "dgy", "alive", "SLOPE", "dcover", "los", "nd",
        "posture 1", "posture 2", "posture 3"]
GEOM = [0, 1, 2, 3]
RESTE = [4, 5, 6, 7, 8, 9, 10, 11]
GRAINES = B.GRAINES_TEST[:3]
pol = charger("cpu"); DEV = next(pol.parameters()).device

def faire(cols):
    def choisir(o, t):
        x = o.clone().to(DEV)
        for c in cols:
            x[:, :, c] = x[torch.randperm(x.shape[0], device=DEV), :, c]
        with torch.no_grad():
            lo, _ = pol(x)
        return lo.argmax(-1).to(o.device), None, None
    return choisir

def taux(cols):
    return sum(B.jouer(B.monde(256, g), faire(cols))[0]["prise"] for g in GRAINES) / len(GRAINES)

ref = taux([])
print("\n  temoin, observation INTACTE : %.1f %%\n" % ref)
print("  %-14s %10s %10s" % ("colonne brouillee", "prise", "chute"))
ch = {}
for c in range(12):
    t = taux([c]); ch[c] = ref - t
    m = "  ⬅ jamais testee le 22/08" if c >= 9 else ""
    print("  %-14s %8.1f %% %9.1f%s" % (NOMS[c], t, ref - t, m))

print("\n  ══ LES DEUX MOITIES, BROUILLEES EN BLOC ══")
g = taux(GEOM); r = taux(RESTE)
print("  les 4 colonnes de GEOMETRIE (apx apy dgx dgy) : %.1f %%   chute %.1f" % (g, ref - g))
print("  les 8 AUTRES, toutes ensemble                 : %.1f %%   chute %.1f" % (r, ref - r))
print("\n  ➤ %s" % ("LA GEOMETRIE SEULE DECIDE — les huit autres, ensemble, ne valent rien."
                    if (ref - r) < 5 and (ref - g) > 15 else
                    "LES AUTRES COLONNES COMPTENT : la conclusion du 22/08 doit etre corrigee."))
