#!/usr/bin/env python3
"""suivre_id — ON SUIT L IDENTIFIANT, PAS LA PLACE. La transition est-elle la ?

Contradiction a lever : aucune transition vivant->mort a identifiant constant SUR UNE PLACE,
mais une entite qui meurt est etiquetee vivante 19,5 % du temps et morte 80,5 %. Donc
l etiquette CHANGE — l entite doit simplement changer de PLACE au moment ou elle meurt.
On la suit par son identifiant, a travers les places.
"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, NP, NC = X.shape
print("=" * 88); print(" SUIVRE L IDENTIFIANT A TRAVERS LES PLACES"); print("=" * 88)
rng = np.random.default_rng(5)

BLOC = 4000
n_ent = n_chg = n_1a0 = n_0a1 = 0
duree_viv, duree_mort = [], []
multi_place = 0
for _ in range(6):
    t = int(rng.integers(0, T - BLOC - 1))
    b = np.asarray(X[t:t + BLOC, :, :]); p = np.asarray(P[t:t + BLOC, :]) > 0.5
    idb, vb = b[..., 0], b[..., 4]
    ids = np.unique(idb[p])
    for u in ids[:: max(1, len(ids) // 300)]:
        msk = p & (idb == u)
        if msk.sum() < 20: continue
        tt, pl = np.nonzero(msk)
        o = np.argsort(tt); tt, pl = tt[o], pl[o]
        v = vb[tt, pl]
        n_ent += 1
        if len(np.unique(pl)) > 1: multi_place += 1
        d = np.diff(v)
        if (d != 0).any():
            n_chg += 1
            n_1a0 += int((d < 0).sum()); n_0a1 += int((d > 0).sum())
        duree_viv.append(int((v > 0.5).sum())); duree_mort.append(int((v < 0.5).sum()))

print("  entites suivies par identifiant ............... %d" % n_ent)
print("  qui occupent PLUSIEURS places ................. %d   (%.1f %%)" % (multi_place, 100 * multi_place / max(n_ent, 1)))
print("  dont `vivant` CHANGE au moins une fois ........ %d   (%.1f %%)" % (n_chg, 100 * n_chg / max(n_ent, 1)))
print("     passages VIVANT -> MORT ⭐ .................. %d" % n_1a0)
print("     passages MORT -> VIVANT (impossible !) ..... %d" % n_0a1)
print("  pas vivants par entite : mediane %.0f | pas morts : mediane %.0f"
      % (np.median(duree_viv), np.median(duree_mort)))
print()
if n_1a0 > 0:
    print("  ✅ LA TRANSITION EXISTE quand on suit l IDENTIFIANT.")
    print("     Le defaut n etait pas le corpus : c est le FENETRAGE PAR PLACE de monde.py.")
    print("     La reparation est donc : indexer par identifiant, pas par colonne.")
else:
    print("  ⛔ meme par identifiant, aucune transition : la cible doit venir de morts.npy.")
if n_0a1 > 0:
    print("  ⚠️ des passages MORT -> VIVANT existent : l etiquette n est pas monotone,")
    print("     donc elle ne peut pas etre lue comme un etat de vie. A instruire avant usage.")
