#!/usr/bin/env python3
"""add_lowcover.py [carte...] — sème du BAS COUVERT procedural (murets/barrieres 0.7-1.4 m,
PASSABLES) dans les cases ouvertes d'un replica, canal 'lowh'. Rend la posture utile.
Deterministe par nom de carte. Sans argument : traite les 7 cartes du benchmark."""
import sys, numpy as np
BASE = "/home/younes/arma3-marl/replica_%s.npz"
MAPS = ["denver", "chicago", "paris", "madrid", "newyork", "london", "lille", "athens", "delphi", "santorini"]
TARGET = 0.08   # fraction des cases OUVERTES couvertes

def do(name):
    f = BASE % name
    d = dict(np.load(f)); GS = int(d["GS"]); solid = d["solid"]
    rng = np.random.default_rng(sum(ord(c) for c in name))     # deterministe
    lowh = np.zeros((GS, GS), np.float32); open_n = int((~solid).sum()); target = int(TARGET * open_n)
    att = 0
    while int((lowh > 0).sum()) < target and att < 40000:
        att += 1
        y = int(rng.integers(2, GS - 2)); x = int(rng.integers(2, GS - 2))
        if solid[y, x]: continue
        L = int(rng.integers(4, 12)); h = float(rng.uniform(0.7, 1.4)); horiz = rng.random() < 0.5
        cells = []
        for k in range(L):
            yy = y + (0 if horiz else k); xx = x + (k if horiz else 0)
            if yy >= GS or xx >= GS or solid[yy, xx]: break
            cells.append((yy, xx))
        if len(cells) < 3: continue
        for (yy, xx) in cells: lowh[yy, xx] = max(lowh[yy, xx], h)
    d["lowh"] = lowh; np.savez(f, **d)
    cov = int((lowh > 0).sum())
    print("  %-10s : bas-couvert %5d cases (%.1f%% ouvert) | h %.1f-%.1f m" %
          (name, cov, 100 * cov / max(1, open_n), float(lowh[lowh > 0].min()) if cov else 0, float(lowh.max()) if cov else 0))

names = sys.argv[1:] if len(sys.argv) > 1 else MAPS
for n in names: do(n)
print("FINI (%d cartes)" % len(names))
