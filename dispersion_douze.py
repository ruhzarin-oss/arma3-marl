#!/usr/bin/env python3
"""UNE COLONNE INERTE N EST IGNOREE QUE SI ELLE VARIE — on le verifie sur les 12.

Trois colonnes de posture rendent EXACTEMENT 0,0 de chute. Un zero exact, trois fois, ne
ressemble pas a « la politique n en tient pas compte » : ca ressemble a « permuter une
constante est l identite ». On mesure la dispersion avant de conclure quoi que ce soit.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger
NOMS = ["apx", "apy", "dgx", "dgy", "alive", "SLOPE", "dcover", "los", "nd",
        "posture 1", "posture 2", "posture 3"]
pol = charger("cpu"); DEV = next(pol.parameters()).device
e = B.monde(256, B.GRAINES_TEST[0]); o = e.reset()
print("\n  actions du monde : %d   (10 = pas de posture ; 13 = avec postures)" % e.n_actions)
print("  sorties de la politique : %d" % pol(o[:1, :1].to(DEV))[0].shape[-1])
ec = [0.0]*12; mn = [1e9]*12; mx = [-1e9]*12; n = 0
for t in range(60):
    for c in range(12):
        col = o[:, :, c]
        ec[c] += float(col.std()); mn[c] = min(mn[c], float(col.min())); mx[c] = max(mx[c], float(col.max()))
    with torch.no_grad():
        a = pol(o.to(DEV))[0].argmax(-1).to(o.device)
    o, _, d, _ = e.step(a, auto_reset=False); n += 1
    if bool(d.all()): break
print("\n  %-12s %12s %10s %10s   %s" % ("colonne", "dispersion", "min", "max", "verdict"))
for c in range(12):
    v = ("CONSTANTE — non testable" if (mx[c]-mn[c]) < 1e-6 else
         ("presque constante" if ec[c]/n < 0.05 else "varie"))
    print("  %-12s %11.3f %10.3f %10.3f   %s" % (NOMS[c], ec[c]/n, mn[c], mx[c], v))
