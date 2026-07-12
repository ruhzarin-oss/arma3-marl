import numpy as np
R = np.load("/home/younes/arma3-marl/stratis_full.npz")
solid = R["solid"]; water = R["water"]; elev = R["elev"]; N = int(R["N"]); W = int(R["W"])


def info(wx, wy):
    c = int(wx / W * (N - 1)); r = int(wy / W * (N - 1))
    if not (0 <= r < N and 0 <= c < N):
        return None
    win = solid[max(r - 3, 0):r + 4, max(c - 3, 0):c + 4]
    wwin = water[max(r - 3, 0):r + 4, max(c - 3, 0):c + 4]
    return (int(water[r, c]), int(elev[r, c]), int(win.sum()), int(wwin.sum()))


cands = {"agia_marina": (2450, 5550), "aerodrome_N": (1750, 6850), "centre": (4100, 4100),
         "sud_ouest": (2800, 3200), "est": (6000, 5200), "actuel": (5569, 4683)}
for k, (x, y) in cands.items():
    inf = info(x, y)
    if inf:
        print("%-14s [%d,%d] -> eau=%d  h=%dm  bati_voisins=%d  eau_voisins=%d" % (k, x, y, inf[0], inf[1], inf[2], inf[3]))
    else:
        print("%-14s [%d,%d] -> hors carte" % (k, x, y))
