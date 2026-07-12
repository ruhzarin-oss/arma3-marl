"""Rend la carte Arma (replica.npz = terrain exporte d'Altis : bati + elevation) en PNG top-down,
oriente nord-en-haut, couvrant le monde [-W,W] x [-W,W]. Sert de FOND a l'overlay furtivite."""
import numpy as np, imageio.v2 as imageio
R = np.load("/home/younes/arma3-marl/replica.npz")
solid = R["solid"].astype("float32"); elev = R["elev"].astype("float32"); GS = solid.shape[0]
e = (elev - elev.min()) / (np.ptp(elev) + 1e-6)
low = np.array([74, 88, 64], dtype="float32"); high = np.array([150, 138, 104], dtype="float32")   # olive -> tan
img = low[None, None] + (high - low)[None, None] * e[..., None]
gy, gx = np.gradient(e)                                                                              # ombrage doux du relief
sh = np.clip(0.78 + (gx - gy) * 6.0, 0.55, 1.15)
img = np.clip(img * sh[..., None], 0, 255)
img[solid > 0.5] = [58, 58, 56]                                                                      # batiments = gris fonce
img = np.flipud(img).astype("uint8")                                                                 # nord en haut
imageio.imwrite("/home/younes/arma3-marl/replica_map.png", img)
print("GS=%d  elev=[%.0f,%.0f]  bati=%.1f%%  shape=%s" % (GS, elev.min(), elev.max(), 100 * (solid > 0.5).mean(), img.shape))
