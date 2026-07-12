"""Rend stratis_full.npz en carte top-down : mer (bleu) + terre (relief olive->tan + ombrage) + batiments (gris)."""
import numpy as np, imageio.v2 as imageio
R = np.load("/home/younes/arma3-marl/stratis_full.npz")
elev = R["elev"].astype("float32"); solid = R["solid"]; water = R["water"]; N = int(R["N"])
land = water < 0.5
lmax = max(float(elev[land].max()) if land.any() else 1.0, 1.0)
e = np.clip(elev / lmax, 0, 1)
low = np.array([72, 100, 58], "float32"); high = np.array([158, 146, 104], "float32")
img = low[None, None] + (high - low)[None, None] * e[..., None]
gy, gx = np.gradient(e)
sh = np.clip(0.85 + (gx - gy) * 4.0, 0.6, 1.25)
img = np.clip(img * sh[..., None], 0, 255)
img[~land] = [120, 170, 226]                      # mer
# liseré de côte (numpy pur) : terre adjacente a l'eau -> teinte sable
sea = ~land; nb = np.zeros_like(land)
nb[1:, :] |= sea[:-1, :]; nb[:-1, :] |= sea[1:, :]; nb[:, 1:] |= sea[:, :-1]; nb[:, :-1] |= sea[:, 1:]
img[nb & land] = [196, 188, 150]
img[solid > 0.5] = [55, 55, 52]                   # batiments
img = np.flipud(img).astype("uint8")
img = np.repeat(np.repeat(img, 4, 0), 4, 1)       # upscale x4
imageio.imwrite("/home/younes/arma3-marl/stratis_map.png", img)
print("carte rendue %s -> stratis_map.png" % str(img.shape))
