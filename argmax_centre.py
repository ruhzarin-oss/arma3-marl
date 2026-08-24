#!/usr/bin/env python3
"""L ARGMAX CENTRE — pre-inscrit dans PREINSCRIPTION_ARGMAX_CENTRE.md (8b687a7).

  P1  l argmax CENTRE de la graine 1 passe de 3,3 % a PLUS DE 25 % sur les graines SELECT
  Falsificateur : sous 10 %, l hypothese du biais qui capture le mode meurt.

⚠️ La premisse de Fable (colinearite biais-compas par secteur d apparition fixe) est DEJA
morte : `assault_terrain.py:287` tire l azimut uniformement sur tout le cercle. Le compas
VARIE. Mais le test reste le bon — et il devient plus interessant : si un biais constant
capture le mode alors que le compas varie, ce n est plus un defaut d identifiabilite des
donnees, c est le reseau qui n a pas appris a s en servir au premier rang.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

ART = [("graine 1 (TOMBE)", "/home/younes/arma3-marl/pol_1200_g1_rejeu_TOMBE.pt"),
       ("graine 0 (PASSE)", "/home/younes/arma3-marl/pol_1200_g0.pt"),
       ("artefact 13/08",   "/home/younes/arma3-marl/boucle_pol.pt")]
SEL = B.GRAINES_SELECT[:3]

print("\n  azimut d apparition fige ? ", getattr(B.monde(4, 0), "fixed_th", None), " (None = tire au hasard sur tout le cercle)")

def logit_moyen(pol, dev):
    """Le vecteur de logits MOYEN sur la propre distribution d etats de la politique."""
    s = torch.zeros(pol.pi.out_features, device=dev); n = 0
    for g in SEL:
        e = B.monde(128, g); o = e.reset()
        for t in range(60):
            with torch.no_grad():
                lo, _ = pol(o.to(dev))
            s += lo.reshape(-1, lo.shape[-1]).sum(0); n += lo.reshape(-1, lo.shape[-1]).shape[0]
            o, _, d, _ = e.step(lo.argmax(-1).to(o.device), auto_reset=False)
            if bool(d.all()): break
    return s / n

def taux(pol, dev, centre):
    def choisir(o, t):
        with torch.no_grad():
            lo, _ = pol(o.to(dev))
        if centre is not None: lo = lo - centre
        return lo.argmax(-1).to(o.device), None, None
    return sum(B.jouer(B.monde(256, g), choisir)[0]["prise"] for g in SEL) / len(SEL)

print("\n  graines SELECT [201..203] — ni apprises, ni jugees\n")
print("  %-20s %14s %18s %10s" % ("artefact", "argmax", "argmax CENTRE", "gain"))
for nom, pt in ART:
    pol = charger("cpu", pt); dev = next(pol.parameters()).device
    c = logit_moyen(pol, dev)
    a = taux(pol, dev, None); b = taux(pol, dev, c)
    print("  %-20s %12.1f %% %16.1f %% %9.1f" % (nom, a, b, b - a))
    if nom.startswith("graine 1"):
        print("       P1 · argmax centre > 25 %% : %s" % ("PASSE" if b > 25 else
              ("⛔ FALSIFICATEUR (< 10 %)" if b < 10 else "zone grise")))
        print("       amplitude du biais retire : %s" % " ".join("%.2f" % float(x) for x in c))
