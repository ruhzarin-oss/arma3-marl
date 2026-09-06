#!/usr/bin/env python3
"""ou_sont_les_morts — meta.json annonce 10 196 morts. Ou sont-elles dans le tenseur ?

Zero transition vivant->mort a identifiant constant sur 4,4 M de paires. Trois hypotheses :
  H1. `presence.all(0)` de monde.py EXCLUT par construction la fenetre qui contient une mort
      (l homme cesse d etre present a l instant ou il meurt) ;
  H2. la mort n est pas un passage 1->0 de `vivant`, mais une DISPARITION du tenseur ;
  H3. elle est ailleurs — dans `morts.npy`.
On tranche sans fenetrage : on lit le tenseur BRUT, place par place, sur des tranches de temps.
"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, NP, NC = X.shape
print("=" * 86); print(" OU SONT LES 10 196 MORTS ?"); print("=" * 86)

print("\n─── morts.npy ───")
try:
    M = np.load(f'{D}/morts.npy')
    print("  forme %s  type %s" % (M.shape, M.dtype))
    print("  extrait :\n", M[:4])
except Exception as e:
    print("  illisible :", e)

print("\n─── le tenseur BRUT, sans fenetrage (20 blocs de 2000 ticks) ───")
rng = np.random.default_rng(5)
n_pres_tot = n_1a0_meme_id = n_1a0_tot = n_dispar_vivant = 0
n_pairs = 0
for _ in range(20):
    t = int(rng.integers(0, T - 2001))
    b = np.asarray(X[t:t + 2000, :, :]); p = np.asarray(P[t:t + 2000, :])
    idb, vb = b[..., 0], b[..., 4]
    a, c = p[:-1] > 0.5, p[1:] > 0.5                      # present en k, en k+1
    deux = a & c
    meme = (idb[:-1] == idb[1:]) & deux
    v0, v1 = vb[:-1], vb[1:]
    n_pairs += deux.sum()
    n_1a0_tot += ((v0 > 0.5) & (v1 < 0.5) & deux).sum()
    n_1a0_meme_id += ((v0 > 0.5) & (v1 < 0.5) & meme).sum()
    n_dispar_vivant += ((v0 > 0.5) & a & ~c).sum()        # vivant en k, ABSENT en k+1
    n_pres_tot += a.sum()
print("  paires (present en k ET en k+1) ......................... %d" % n_pairs)
print("  passages vivant->mort, TOUTES paires .................... %d" % n_1a0_tot)
print("  passages vivant->mort A IDENTIFIANT CONSTANT ⭐ .......... %d" % n_1a0_meme_id)
print("  VIVANT en k puis ABSENT en k+1 (disparition) ............ %d" % n_dispar_vivant)
print("\n  LECTURE :")
if n_1a0_meme_id > 0:
    print("   -> les morts EXISTENT comme passage 1->0 a identifiant constant.")
    print("      C est donc le fenetrage `presence.all(0)` de monde.py qui les excluait (H1).")
else:
    print("   -> AUCUN passage 1->0 a identifiant constant, meme sans fenetrage.")
    print("      La mort n est PAS un passage de `vivant` : c est une DISPARITION (H2),")
    print("      et toute cible batie sur `1 - vivant[k+1]` est structurellement vide.")
