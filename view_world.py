#!/usr/bin/env python3
"""view_world.py — visu 3D du monde (relief + batiments) directement depuis world_<nom>.npz.
Matplotlib, aucune dependance Isaac -> garanti. Preuve visuelle que la conversion est bonne."""
import argparse, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="athens"); ap.add_argument("--dir", default="/home/younes/arma3-marl")
a = ap.parse_args()
W = np.load("%s/world_%s.npz" % (a.dir, a.name))
hf = W["heightfield"]; Wm = float(W["W"]); boxes = W["boxes"]; G = hf.shape[0]
xs = (np.arange(G) / (G - 1) - 0.5) * 2 * Wm
step = max(1, G // 100)
X, Y = np.meshgrid(xs[::step], xs[::step]); Z = hf[::step, ::step]

fig = plt.figure(figsize=(13, 9)); ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(X, Y, Z, cmap="terrain", alpha=0.8, linewidth=0, antialiased=True, rstride=1, cstride=1)

def faces(cx, cy, cz, sx, sy, sz):
    x0, x1 = cx - sx / 2, cx + sx / 2; y0, y1 = cy - sy / 2, cy + sy / 2; z0, z1 = cz - sz / 2, cz + sz / 2
    v = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    return [[v[4], v[5], v[6], v[7]], [v[0], v[1], v[5], v[4]], [v[2], v[3], v[7], v[6]], [v[1], v[2], v[6], v[5]], [v[0], v[3], v[7], v[4]]]

polys = []
for b in boxes:
    polys += faces(*b)
ax.add_collection3d(Poly3DCollection(polys, facecolor="#b5651d", edgecolor="#5a3010", linewidth=0.15, alpha=0.97))

ax.set_box_aspect((1, 1, 0.3)); ax.view_init(elev=42, azim=-58)
ax.set_xlabel("m"); ax.set_ylabel("m"); ax.set_zlabel("m")
ax.set_title("%s — monde physique : relief %d m + %d batiments" % (a.name.capitalize(), int(hf.max() - hf.min()), len(boxes)))
out = "%s/view_%s.png" % (a.dir, a.name)
plt.savefig(out, dpi=115, bbox_inches="tight"); print("ecrit", out)
