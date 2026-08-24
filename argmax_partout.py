#!/usr/bin/env python3
"""L ARGMAX EST-IL MAUVAIS PARTOUT, OU SEULEMENT POUR LA GRAINE PERDANTE ?

Si echantillonner bat l argmax sur TOUTES les politiques, alors la loterie de 23 h 15
n est pas une instabilite de l ENTRAINEMENT : c est une instabilite de la LECTURE, et le
banc lisait mal depuis le debut. Trois artefacts, memes graines de test, meme code.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

ART = [("graine 1 (TOMBE)", "/home/younes/arma3-marl/pol_1200_g1_rejeu_TOMBE.pt"),
       ("graine 0 (PASSE)", "/home/younes/arma3-marl/pol_1200_g0.pt"),
       ("artefact du 13/08", "/home/younes/arma3-marl/boucle_pol.pt")]

def taux(pol, dev, argmax):
    def choisir(o, t):
        with torch.no_grad():
            lo, _ = pol(o.to(dev))
        a = lo.argmax(-1) if argmax else torch.distributions.Categorical(logits=lo).sample()
        return a.to(o.device), None, None
    v = [B.jouer(B.monde(256, g), choisir)[0]["prise"] for g in B.GRAINES_TEST]
    return sum(v) / len(v)

print("\n  graines de TEST, memes pour tous\n")
print("  %-20s %10s %18s %10s" % ("artefact", "argmax", "echantillonnage", "ecart"))
for nom, pt in ART:
    try:
        pol = charger("cpu", pt)
    except Exception as e:
        print("  %-20s  absent (%s)" % (nom, type(e).__name__)); continue
    dev = next(pol.parameters()).device
    a = taux(pol, dev, True); e = taux(pol, dev, False)
    print("  %-20s %8.1f %% %16.1f %% %8.1f" % (nom, a, e, e - a))
print("\n  ⚠️ Si l ecart est positif PARTOUT, la porte lisait mal — et la loterie de")
print("     23 h 15 mesurait la LECTURE, pas l entrainement.")
