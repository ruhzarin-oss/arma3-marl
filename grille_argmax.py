#!/usr/bin/env python3
"""LA GRILLE 2x2 — pre-inscrite dans PREINSCRIPTION_ARGMAX.md (ca2f7e7), AVANT l artefact.

Le 44,1 % de l entrainement et le 3,3 % de la porte different par DEUX choses a la fois :
la facon de decider (echantillonner / argmax) et les graines (entrainement / test).
On mesure les quatre cases avec le MEME code, sur le MEME artefact conserve.

  D1  echantillonner sur graines de TEST rend > 30 %  -> c est l ARGMAX qui degenere
  D2  argmax sur graines d ENTRAINEMENT rend < 10 %   -> il echoue meme la ou elle a appris
  Falsificateur : si D < 10 %, echantillonner ne sauve rien — c est du SUR-APPRENTISSAGE,
  et l entropie n y ferait rien.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

PT = "/home/younes/arma3-marl/pol_1200_g1_rejeu_TOMBE.pt"
pol = charger("cpu", PT); DEV = next(pol.parameters()).device
print("\n  artefact : %s" % PT.split("/")[-1])
print("  sorties  : %d actions" % pol.pi.out_features)

def bras(argmax):
    def choisir(o, t):
        with torch.no_grad():
            lo, _ = pol(o.to(DEV))
        if argmax:
            a = lo.argmax(-1)
        else:
            a = torch.distributions.Categorical(logits=lo).sample()
        return a.to(o.device), None, None
    return choisir

def taux(graines, argmax):
    v = [B.jouer(B.monde(256, g), bras(argmax))[0]["prise"] for g in graines]
    return sum(v) / len(v)

TR = B.GRAINES_TRAIN[:6]; TE = B.GRAINES_TEST
print("\n  %-22s %16s %16s" % ("", "graines ENTRAINEMENT", "graines TEST"))
A = taux(TR, True);  Bx = taux(TE, True)
C = taux(TR, False); D = taux(TE, False)
print("  %-22s %14.1f %% %14.1f %%" % ("argmax", A, Bx))
print("  %-22s %14.1f %% %14.1f %%" % ("echantillonnage", C, D))
print("\n  D1 · D > 30 %%  (echantillonner sur test)      : %.1f %%  -> %s"
      % (D, "PASSE" if D > 30 else "ECHOUE"))
print("  D2 · A < 10 %%  (argmax sur entrainement)      : %.1f %%  -> %s"
      % (A, "PASSE" if A < 10 else "ECHOUE"))
print()
if D > 30 and A < 10:
    print("  ➤ DEGENERESCENCE DE L ARGMAX. La politique a appris une strategie MIXTE :")
    print("    la figer la detruit, et ca n a rien a voir avec les graines.")
elif D < 10:
    print("  ⛔ FALSIFICATEUR : echantillonner ne sauve rien. Ce n est pas l argmax,")
    print("    c est un SUR-APPRENTISSAGE aux graines d entrainement.")
elif D > 30 and A > 30:
    print("  ⛔ L argmax marche sur les graines VUES et pas sur les autres :")
    print("    c est encore du sur-apprentissage, sous un autre visage.")
else:
    print("  ⚠️ AUCUN DES CAS ECRITS. On l ecrit tel quel, on n invente pas d explication.")
