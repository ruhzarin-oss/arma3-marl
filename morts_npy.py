#!/usr/bin/env python3
"""morts_npy — la mort n est pas dans les noeuds. Ou est-elle, et comment s en servir ?"""
import numpy as np, json
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
M = np.load(f'{D}/morts.npy'); T = X.shape[0]
print("=" * 84); print(" 1. `vivant` EST-IL CONSTANT PAR ENTITE ?"); print("=" * 84)
rng = np.random.default_rng(5); chg = 0; vus = 0
for _ in range(12):
    t = int(rng.integers(0, T - 3001))
    b = np.asarray(X[t:t + 3000, :, :]); p = np.asarray(P[t:t + 3000, :]) > 0.5
    idb, vb = b[..., 0], b[..., 4]
    for pl in range(0, b.shape[1], 7):
        i, v, m = idb[:, pl], vb[:, pl], p[:, pl]
        if m.sum() < 10: continue
        for u in np.unique(i[m]):
            s = v[m & (i == u)]
            vus += 1; chg += int(len(np.unique(s)) > 1)
print("  entites suivies : %d   dont `vivant` CHANGE : %d  (%.2f %%)" % (vus, chg, 100 * chg / max(vus, 1)))
print("  -> %s" % ("`vivant` est une ETIQUETTE FIXE par entite, pas un etat qui evolue."
                   if chg == 0 else "il evolue parfois, a instruire"))
print()
print("=" * 84); print(" 2. LE CONTENU DE morts.npy"); print("=" * 84)
print("  forme %s  type %s" % (M.shape, M.dtype))
meta = json.load(open(f'{D}/meta.json'))
print("  cles de meta.json :", [k for k in meta])
for k in meta:
    if 'mort' in k.lower(): print("     %s = %s" % (k, meta[k]))
print("\n  %-6s %12s %12s %12s %12s" % ("col", "min", "max", "moyenne", "n valeurs"))
for c in range(M.shape[1]):
    v = M[:, c]; print("  %-6d %12.2f %12.2f %12.2f %12d" % (c, v.min(), v.max(), v.mean(), len(np.unique(v))))
print("\n  20 premieres lignes :"); print(M[:20])
print("\n  part de -1 par colonne :", [float((M[:, c] == -1).mean().round(3)) for c in range(M.shape[1])])
