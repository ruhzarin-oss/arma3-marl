#!/usr/bin/env python3
"""OU L ARGMAX DE LA GRAINE 1 CALE-T-IL, ET QUE CHOISIT-IL LA ?

Ni l entropie ni la dispersion ne separent la graine 1 des deux autres : l artefact du
13/08 est presque aussi plat (1,525 contre 1,654) et groupe MEME PLUS (22,3 m contre 23,0),
et son argmax rend pourtant 50,7 %. Le recit « continuum de nettete » et le recit
« portefeuille » sont donc tous les deux insuffisants.

Reste la question spatiale, que Fable avait posee et que je n avais pas faite :
OU cale-t-elle, et QUELLE action l argmax choisit-il a cet endroit ?
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

NOMS = {0:"N", 1:"NE", 2:"E", 3:"SE", 4:"S", 5:"SO", 6:"O", 7:"NO", 8:"TENIR", 9:"APPUYER"}
ART = [("graine 1 (TOMBE)", "/home/younes/arma3-marl/pol_1200_g1_rejeu_TOMBE.pt"),
       ("graine 0 (PASSE)", "/home/younes/arma3-marl/pol_1200_g0.pt")]

for nom, pt in ART:
    pol = charger("cpu", pt); dev = next(pol.parameters()).device
    for tau in (0, 1.0):
        e = B.monde(256, B.GRAINES_TEST[0]); o = e.reset()
        hist = torch.zeros(10); prof = []
        for t in range(60):
            with torch.no_grad():
                lo, _ = pol(o.to(dev))
            a = lo.argmax(-1) if tau == 0 else torch.distributions.Categorical(logits=lo/tau).sample()
            a = a.to(o.device)
            viv = e._aalive()
            for k in range(10):
                hist[k] += float(((a == k) & viv).sum())
            if t % 15 == 0 or t == 59:
                prof.append((t, float(torch.sqrt(e.apx**2 + e.apy**2).mean()), float(viv.float().sum(1).mean())))
            o, _, d, _ = e.step(a, auto_reset=False)
            if bool(d.all()): break
        h = 100.0 * hist / hist.sum()
        top = sorted(range(10), key=lambda k: -h[k])[:4]
        print("\n  %-18s %s" % (nom, "ARGMAX" if tau == 0 else "tau = 1 (echantillonne)"))
        print("     actions : %s" % "  ".join("%s %.0f%%" % (NOMS[k], h[k]) for k in top))
        print("     profil  : %s" % "  ".join("pas %d : %.0f m, %.1f vivants" % p for p in prof))
