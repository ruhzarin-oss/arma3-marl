#!/usr/bin/env python3
"""certify_map — cartographie le replica pour trouver un COEUR BÂTI où poser l'objectif (couvert jusqu'à l'objectif)."""
import numpy as np
R = np.load("/home/younes/arma3-marl/replica.npz")
solid = R["solid"]; GS = int(R["GS"]); W = float(R["W"]); obj = R["obj"]
mpp = W / GS
print("W(m)=%.0f  GS=%d  -> %.2f m/cellule ; obj(world)=%s" % (W, GS, mpp, obj))


def w2g(px, py):
    gx = int((px / W + 0.5) * (GS - 1)); gy = int((py / W + 0.5) * (GS - 1))
    return gx, gy


def dens(cxg, cyg, r):
    ys, xs = np.ogrid[:GS, :GS]
    m = ((xs - cxg) ** 2 + (ys - cyg) ** 2) <= r * r
    return solid[m].mean() if m.any() else 0.0


og = w2g(0.0, 0.0)
print("origine sandbox (0,0) -> grille %s | densité bâti r=25m: %.2f  r=70m: %.2f" % (
    og, dens(og[0], og[1], int(25 / mpp)), dens(og[0], og[1], int(70 / mpp))))

B = GS // 10
grid = np.zeros((10, 10))
for i in range(10):
    for j in range(10):
        grid[i, j] = solid[i * B:(i + 1) * B, j * B:(j + 1) * B].mean()
np.set_printoptions(precision=2, suppress=True, linewidth=120)
print("densité bâti par bloc (ligne=Y grille, col=X grille) :")
print(grid)

# CANDIDAT : un centre où densité(r=25) est FAIBLE (petite cour/place pour poser l'objectif) MAIS densité(r=70) FORTE
# (couvert continu sur l'approche jusqu'à ~30m) — le contraire de la clairière actuelle.
print("\ncandidats (cour ~ouverte, approche ~bâtie) — world (x,y) | dens25 dens70 :")
cand = []
for gy in range(15, GS - 15, 6):
    for gx in range(15, GS - 15, 6):
        d25 = dens(gx, gy, int(25 / mpp)); d70 = dens(gx, gy, int(70 / mpp))
        wx = (gx / (GS - 1) - 0.5) * W; wy = (gy / (GS - 1) - 0.5) * W
        # cour jouable : pas full-bâti au centre (d25<0.55) mais approche dense (d70>0.5)
        if 0.15 < d25 < 0.55 and d70 > 0.5:
            cand.append((d70 - d25, wx, wy, d25, d70))
cand.sort(reverse=True)
for sc, wx, wy, d25, d70 in cand[:8]:
    print("  world=(%6.1f,%6.1f) | dens25=%.2f dens70=%.2f | contraste=%.2f" % (wx, wy, d25, d70, sc))
