#!/usr/bin/env python3
"""CANDIDAT A — LA POLITIQUE LIT-ELLE LA PENTE ? Ablation A L EVALUATION, zero entrainement.

Pre-inscription : PREINSCRIPTION_DEUX_CANDIDATS.md (commit 82101f9), ecrite AVANT.
  A1  l ecart de taux de prise entre INTACT et BROUILLE est < 3 points
  A2  il reste < 3 points sur au moins 2 graines sur 3
  Falsificateur : si l ecart depasse 3 points, la politique LIT la pente.

⚠️ ON PERMUTE, ON NE RETIRE PAS. Retirer la colonne changerait la taille de l entree et le
reseau ne saurait plus lire — on casserait l instrument au lieu de tuer l information.
La pente est la COLONNE 5 de l observation (`assault_terrain.py:519`, base =
[apx, apy, dgx, dgy, alive, SLOPE, dcover, los, nd]).
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger, COLS

COL_PENTE = 5
GRAINES = B.GRAINES_TEST[:3]
pol = charger("cpu")
DEV = next(pol.parameters()).device
print("politique sur %s   colonnes lues : %s   pente = colonne %d" % (DEV, COLS, COL_PENTE))

def faire(brouille):
    def choisir(o, t):
        x = o.clone().to(DEV)
        if brouille:
            # ⚠️ PERMUTATION ENTRE ENVIRONNEMENTS : chaque agent recoit la pente d un autre
            # monde. La colonne garde sa loi marginale ; elle perd tout lien avec SA position.
            n = x.shape[0]
            x[:, :, COL_PENTE] = x[torch.randperm(n, device=DEV), :, COL_PENTE]
        # Le gymnase rend DEJA les 12 colonnes que lit la politique (base 9 + posture 3) ;
        # COLS ne sert qu a projeter le canal Arma a 18. On verifie, on ne suppose pas.
        with torch.no_grad():
            lo, _ = pol(x if x.shape[-1] == len(COLS) else x[:, :, COLS])
        return lo.argmax(-1).to(o.device), None, None
    return choisir

print("largeur obs du gymnase :", B.monde(4, 0).reset().shape[-1], "colonnes")
print("\n%-8s %12s %12s %10s" % ("graine", "intact", "brouille", "ecart"))
ecarts = []
for g in GRAINES:
    a, *_ = B.jouer(B.monde(256, g), faire(False))
    b, *_ = B.jouer(B.monde(256, g), faire(True))
    d = a["prise"] - b["prise"]
    ecarts.append(abs(d))
    print("%-8d %11.1f %% %11.1f %% %9.1f" % (g, a["prise"], b["prise"], d))
m = sum(ecarts) / len(ecarts)
print("\n  ecart moyen : %.1f points   (seuil pre-inscrit : 3,0)" % m)
print("  A1 · ecart moyen < 3 pts        : %s" % ("PASSE" if m < 3 else "ECHOUE"))
sous = sum(1 for e in ecarts if e < 3)
print("  A2 · < 3 pts sur >= 2 graines/3 : %s  (%d sur 3)" % ("PASSE" if sous >= 2 else "ECHOUE", sous))
print()
if m < 3 and sous >= 2:
    print("  ➤ LA POLITIQUE EST AVEUGLE A LA PENTE. Brouiller la colonne ne change rien :")
    print("    elle ne l a jamais apprise, parce que rien ne l a jamais payee.")
else:
    print("  ⛔ FALSIFICATEUR : la politique LIT la pente. Le candidat A change de sens —")
    print("    elle la lit SANS la payer, donc la lui faire payer devient un levier reel.")
