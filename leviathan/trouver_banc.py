#!/usr/bin/env python3
"""trouver_banc.py — trouve la bande la plus PLATE pour le banc de tir, en local.

Emprise du banc : 6 duels alignes sur X (espaces de --pas), les cibles a +Y jusqu a
200 m, plus une marge de securite au-dela pour que les balles perdues finissent dans
le vide et non dans le duel suivant.
"""
import sys, argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--monde", default="altis")
ap.add_argument("--pas", type=int, default=300, help="ecart entre duels (m)")
ap.add_argument("--n", type=int, default=6, help="duels par bande")
ap.add_argument("--marge", type=int, default=400, help="degagement derriere les cibles (m)")
a = ap.parse_args()

d = np.load("/home/younes/arma3-marl/leviathan/relief_%s.npz" % a.monde)
H, EAU, res = d["H"], d["EAU"], int(d["pas"])
n = H.shape[0]
larg = int(np.ceil(((a.n - 1) * a.pas) / res)) + 1
prof = int(np.ceil((200 + a.marge) / res)) + 1
print("=== recherche d une bande %d x %d m (%d x %d cases de %d m) ===" % (
    (a.n - 1) * a.pas, 200 + a.marge, larg, prof, res), flush=True)

cands = []
for j in range(n - prof):
    for i in range(n - larg):
        f = H[j:j + prof, i:i + larg]
        e = EAU[j:j + prof, i:i + larg]
        if e.any() or np.isnan(f).any():
            continue
        cands.append((float(f.max() - f.min()), float(f.std()), i * res, j * res))
cands.sort()
print("les 10 bandes les plus plates (toutes sur terre) :", flush=True)
print("%10s %8s   %s" % ("denivele", "ecart", "zone"), flush=True)
for rel, sd, x, y in cands[:10]:
    print("%8.0f m %8.1f   --zone %d,%d" % (rel, sd, x, y), flush=True)
if cands:
    rel, sd, x, y = cands[0]
    print("\n>>> --zone %d,%d --pas %d   (denivele %.0f m sur toute l emprise)" % (x, y, a.pas, rel), flush=True)
    print(">>> %s" % ("PLAT : utilisable" if rel <= 12 else
                      "encore %0.f m de denivele : verifier duel par duel" % rel), flush=True)
else:
    print("aucune bande entierement sur terre a cette taille - reduire --pas", flush=True)
