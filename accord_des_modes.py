#!/usr/bin/env python3
"""LE FILM MESURE LA PERFORMANCE DU MODE, PAS SON IDENTITE ⟨Fable, 24/08⟩.

Deux structures restent compatibles avec les 24 points : un mode VERROUILLE tot et mauvais,
ou un mode qui ERRE entre plusieurs mauvais sans jamais traverser un bon. C est la seule
mesure qui separe « bifurcation » de « marche aleatoire », et elle coute des minutes.

Accord d argmax entre points : fraction des etats ou l action de rang 1 est IDENTIQUE entre
deux points de sauvegarde. Verrouille -> accord eleve entre points eloignes. Errant -> bas.

⚠️ Les etats sont ceux d une trajectoire de REFERENCE commune (celle du point final), pour
que les deux politiques soient comparees sur les MEMES entrees.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

PTS = [100, 300, 700, 1150]
SEL = B.GRAINES_SELECT[:2]

def etats(pol, dev, n=128):
    """Collecte les observations le long de la trajectoire argmax du point FINAL."""
    O = []
    for g in SEL:
        e = B.monde(n, g); o = e.reset()
        for t in range(60):
            O.append(o.clone())
            with torch.no_grad():
                lo, _ = pol(o.to(dev))
            o, _, d, _ = e.step(lo.argmax(-1).to(o.device), auto_reset=False)
            if bool(d.all()): break
    return torch.cat([x.reshape(-1, x.shape[-1]) for x in O])

for G in (0, 1):
    ref = charger("cpu", "/mnt/data/film_g%d/it1150.pt" % G)
    dev = next(ref.parameters()).device
    X = etats(ref, dev)
    A = {}
    for it in PTS:
        p = charger("cpu", "/mnt/data/film_g%d/it%04d.pt" % (G, it))
        with torch.no_grad():
            A[it] = p(X.to(dev))[0].argmax(-1)
    print("\n  ══ GRAINE %d — accord d argmax entre points (%d etats) ══\n" % (G, len(X)))
    print("       %s" % "".join("%9d" % it for it in PTS))
    for a in PTS:
        l = "  %4d " % a
        for b in PTS:
            l += "%8.0f %%" % (100.0 * float((A[a] == A[b]).float().mean()))
        print(l)
print("\n  ⚠️ Accord ELEVE entre points eloignes = mode VERROUILLE tot (bifurcation).")
print("     Accord BAS = mode ERRANT : la region des bons modes est simplement petite.")
