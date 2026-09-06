#!/usr/bin/env python3
"""sonde_identite — LE DEUXIEME DEFAUT, independant du decalage.

`monde.py` suit des PLACES (`sel` = indices de colonnes), pas des ENTITES. `meta.json` dit
577 places pour 10 034 identifiants sur la nuit : une place est donc RECYCLEE. `presence.all(0)`
garantit que la place est occupee tout du long — PAS qu elle l est par le meme soldat.
Si l identifiant change au milieu d une tranche, le « deplacement » a predire n est pas un
deplacement : c est un saut entre DEUX HOMMES DIFFERENTS.
"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, NP, NC = X.shape
LEN, NE, NFEN = 24, 32, 3000
rng = np.random.default_rng(11)
print("=" * 86); print(" SONDE IDENTITE — les tranches suivent-elles le MEME homme ?"); print("=" * 86)
ids, xy, n, ess = [], [], 0, 0
while n < NFEN and ess < NFEN * 8:
    ess += 1
    t = int(rng.integers(0, T - LEN - 1)); pres = np.asarray(P[t:t + LEN])
    ok = np.where(pres.all(0))[0]
    if len(ok) < 4: continue
    sel = ok if len(ok) <= NE else rng.choice(ok, NE, replace=False)
    b = np.asarray(X[t:t + LEN, sel, :])
    ids.append(b[..., 0]); xy.append(b[..., 1:3]); n += 1
ids = np.concatenate([i.reshape(LEN, -1).T for i in ids])          # (traces, LEN)
xy = np.concatenate([v.reshape(LEN, -1, 2).transpose(1, 0, 2) for v in xy])
print("  %d traces de %d pas\n" % (len(ids), LEN))
change = (ids[:, 1:] != ids[:, :-1])
print("  traces ou l identifiant CHANGE au moins une fois : %.2f %%" % (100 * change.any(1).mean()))
print("  pas ou l identifiant change                      : %.2f %%" % (100 * change.mean()))
print("  identifiants distincts par trace : moyenne %.2f, maximum %d"
      % (np.mean([len(np.unique(r)) for r in ids]), max(len(np.unique(r)) for r in ids)))
d = np.linalg.norm(xy[:, 1:] - xy[:, :-1], axis=-1)
print("\n  deplacement par pas, quand l identifiant NE change PAS : mediane %8.2f  p99 %10.2f"
      % (np.median(d[~change]), np.percentile(d[~change], 99)))
if change.any():
    print("  deplacement par pas, quand l identifiant CHANGE ......  mediane %8.2f  p99 %10.2f"
          % (np.median(d[change]), np.percentile(d[change], 99)))
    print("\n  -> ces sauts ne sont pas des deplacements : ce sont DEUX HOMMES DIFFERENTS.")
    print("     Ils entrent dans `err` ET dans `err_pers` a l identique, donc ils GONFLENT les")
    print("     deux et ecrasent l ecart entre un modele et un temoin. C est la seconde raison")
    print("     pour laquelle le banc ne separait pas un crochet d une ligne droite.")
else:
    print("\n  -> aucun changement d identifiant : ce defaut-la n existe pas.")
