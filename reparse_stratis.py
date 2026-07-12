"""Re-parse le RPT COMPLET (pas la fenetre 500 Ko du pont) pour reconstruire stratis_full.npz :
relief (160x160, dernier run = 160 valeurs/ligne) + batiments (HMT_BLD) + eau."""
import re, numpy as np
L = "/mnt/data/harmattan-sandbox/logs/server14.out"
N = 160; ws = 8192
lines = open(L, encoding="utf-8", errors="ignore").read().splitlines()
elev_rows = {}
for ln in lines:
    m = re.search(r"HMT_ELEV (\d+) \[([^\]]*)\]", ln)
    if m:
        r = int(m.group(1)); vals = m.group(2).split(",")
        if len(vals) == N: elev_rows[r] = [float(v) for v in vals]   # dernier run (160 val) gagne par index
elev = np.zeros((N, N), dtype="float32")
for r, v in elev_rows.items():
    if r < N: elev[r] = v
pts = []
for ln in lines:
    if "HMT_BLD " in ln:
        for a, bv in re.findall(r"(-?\d+);(-?\d+)\|", ln): pts.append((int(a), int(bv)))
solid = np.zeros((N, N), dtype="float32")
for (bx, by) in pts:
    c = min(max(int(bx / ws * (N - 1)), 0), N - 1); r = min(max(int(by / ws * (N - 1)), 0), N - 1); solid[r, c] = 1.0
water = (elev <= 0).astype("float32")
np.savez("/home/younes/arma3-marl/stratis_full.npz", elev=elev, solid=solid, water=water, N=N, W=ws)
print("relief lignes=%d elev[%d..%d] | bati pts=%d cells=%.1f%% | eau=%.1f%%" % (
    len(elev_rows), int(elev.min()), int(elev.max()), len(pts), 100 * solid.mean(), 100 * water.mean()))
