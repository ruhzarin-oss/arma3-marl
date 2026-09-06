#!/usr/bin/env python3
"""part_erreur — QUELLE PART DE L ERREUR PUBLIEE VIENT DES SAUTS D IDENTITE ?"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T = X.shape[0]; LEN, NE, NFEN = 24, 32, 3000
rng = np.random.default_rng(11); ids, xy, n, ess = [], [], 0, 0
while n < NFEN and ess < NFEN * 8:
    ess += 1
    t = int(rng.integers(0, T - LEN - 1)); pres = np.asarray(P[t:t + LEN])
    ok = np.where(pres.all(0))[0]
    if len(ok) < 4: continue
    sel = ok if len(ok) <= NE else rng.choice(ok, NE, replace=False)
    b = np.asarray(X[t:t + LEN, sel, :])
    ids.append(b[..., 0].reshape(LEN, -1).T); xy.append(b[..., 1:3].reshape(LEN, -1, 2).transpose(1, 0, 2)); n += 1
ids = np.concatenate(ids); xy = np.concatenate(xy)
ch = ids[:, 1:] != ids[:, :-1]
d2 = ((xy[:, 1:] - xy[:, :-1]) ** 2).sum(-1)
tot = d2.sum()
print("=" * 82); print(" PART DE L ERREUR QUI VIENT DES SAUTS D IDENTITE"); print("=" * 82)
print("  pas concernes par un saut          : %6.2f %% des pas" % (100 * ch.mean()))
print("  part de l ERREUR QUADRATIQUE totale : %6.3f %%" % (100 * d2[ch].sum() / tot))
print("  part restante, le VRAI mouvement    : %6.3f %%" % (100 * d2[~ch].sum() / tot))
print("\n  erreur quadratique moyenne par pas :")
print("     avec saut  %14.1f" % d2[ch].mean())
print("     sans saut  %14.4f" % d2[~ch].mean())
print("     rapport    %14.0f x" % (d2[ch].mean() / max(d2[~ch].mean(), 1e-9)))
print("\n  -> `err` et `err_pers` sont l un et l autre DOMINES par les memes sauts, donc ils")
print("     se touchent a la quatrieme decimale (0,015829 contre 0,015786) quel que soit le")
print("     modele. Le juge ne pouvait PAS separer un crochet d une ligne droite : le vrai")
print("     mouvement pese %.3f %% de ce qu il mesure." % (100 * d2[~ch].sum() / tot))
