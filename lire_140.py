#!/usr/bin/env python3
"""P3 — LA LECTURE QUI MANQUAIT AU CHIFFRE FONDATEUR.

Le "5,7 %" a 140 iterations a ouvert tout le dossier « le protocole ne retrouve plus le
13/08 ». Il n a JAMAIS eu de lecture echantillonnee : a l epoque le torch.save vivait dans
le if de la porte et l artefact etait jete.

Prediction P3, deposee le 24/08 a 13 h (8b687a7) : sa lecture echantillonnee sort
AU-DESSUS DE 20 %. Si elle passe, le premier dossier se re-etiquette « artefact de budget
plus artefact de lecture », et l enigme se dissout.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger
pol = charger("cpu", "/home/younes/arma3-marl/pol_140_reference_TOMBE.pt")
dev = next(pol.parameters()).device

def taux(argmax, graines):
    def choisir(o, t):
        with torch.no_grad():
            lo, _ = pol(o.to(dev))
        a = lo.argmax(-1) if argmax else torch.distributions.Categorical(logits=lo).sample()
        return a.to(o.device), None, None
    return sum(B.jouer(B.monde(256, g), choisir)[0]["prise"] for g in graines) / len(graines)

for nom, gr in (("TEST  [101-106]", B.GRAINES_TEST), ("SELECT[201-203]", B.GRAINES_SELECT[:3])):
    a = taux(True, gr); e = taux(False, gr)
    print("\n  %s   argmax %.1f %%   echantillonne %.1f %%" % (nom, a, e))
e = taux(False, B.GRAINES_TEST)
print("\n  P3 · lecture echantillonnee > 20 %% : %.1f %%  ->  %s"
      % (e, "PASSE" if e > 20 else "⛔ ECHOUE"))
print("  (pour memoire : frontale 12,8 %%, flanc 34,3 %%, artefact du 13/08 echantillonne 31,5 %%)")
