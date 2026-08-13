#!/usr/bin/env python3
"""porte_monde — LA PORTE DU CHANGEMENT DE MONDE, avec le BON echantillonnage.

⚠️ MA PREMIERE PORTE COMPARAIT DEUX ECHANTILLONNAGES DIFFERENTS : les pentes du gymnase SOUS
LES PIEDS DES AGENTS (qui naissent tous a la meme distance de l objectif) contre celles de
Stratis a des points TIRES AU HASARD sur toute la carte. Les agents ne se tiennent pas dans les
plaines : le p01 restait haut alors que le terrain, lui, en contenait.

On echantillonne donc le gymnase COMME Stratis : des cellules tirees au hasard sur la carte.
Meme grandeur, meme formule, MEME ECHANTILLONNAGE — c est la troisieme condition, et je l avais
oubliee deux fois aujourd hui.
"""
import sys, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

S = np.sort(np.load("/home/younes/arma3-marl/pentes_stratis.npy"))
qS = lambda p: float(S[int(p * (len(S) - 1))])
e = AssaultTerrain(num_envs=256, seed=5, device="cuda:0", max_steps=10, **MONDE_ARMA)
e.reset()
# LA MEME LOI DE TIRAGE QUE LA SONDE STRATIS : des cellules au hasard, partout sur la carte.
sl = (e.slope / 5.0).reshape(-1)
idx = torch.randint(0, sl.numel(), (4000,), device=sl.device)
v = sorted(sl[idx].tolist()); qG = lambda p: v[int(p * (len(v) - 1))]

print("\n  LA PORTE DU CHANGEMENT — memes formules, MEME echantillonnage")
print(f"    {'quantile':<10}{'STRATIS':>10}{'GYMNASE':>10}   verdict")
print("  " + "-" * 46)
ok = True
for nom, p in (("p01", 0.01), ("median", 0.5), ("p99", 0.99)):
    c, g = qS(p), qG(p)
    if c < 1e-6:
        passe = abs(g - c) < 0.05
        print(f"    {nom:<10}{c:>10.3f}{g:>10.3f}   {'PASSE' if passe else 'TOMBE'}  (ecart absolu {abs(g-c):.3f})")
    else:
        passe = abs(g - c) / c <= 0.15
        print(f"    {nom:<10}{c:>10.3f}{g:>10.3f}   {'PASSE' if passe else 'TOMBE'}  ({100*(g-c)/c:+.0f} %)")
    ok &= passe
print("  " + "-" * 46)
print("    " + ("LA PORTE EST FRANCHIE — le monde d entrainement suit la carte."
                if ok else "NON FRANCHIE : on cherche pourquoi, on n ajuste pas."))
sys.exit(0 if ok else 1)
