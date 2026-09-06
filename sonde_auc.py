#!/usr/bin/env python3
"""sonde_auc — QUE MESURE REELLEMENT LE 0,9996 ? On repond par mesure, pas par lecture de code.

TROIS SOUPCONS, chacun testable sans entrainer quoi que ce soit :
  S1. LE REMPLISSAGE. `pm` et `ym` sont TOUS DEUX multiplies par le masque, donc chaque
      emplacement vide devient (prediction 0, cible 0) : un negatif parfaitement classe sous
      tous les positifs. Si le remplissage domine, l AUC mesure la forme du tenseur.
  S2. LA CIBLE. `1 - vivant[k+1]` dit « EST-IL MORT », pas « VA-T-IL MOURIR ». Un mort au pas
      k reste mort au pas k+1. La vraie cible est la TRANSITION : vivant en k, mort en k+1.
  S3. LE TEMOIN TRIVIAL. Un predicteur qui recopie « mort en k » — zero parametre, zero
      apprentissage — quelle AUC obtient-il sur la MEME cible ?

Aucun modele n est charge : on n a besoin QUE des donnees et du temoin trivial. Si le temoin
trivial atteint deja 0,999, le 0,9996 du modele ne vaut rien, et c est demontre sans GPU.
"""
import numpy as np, time

D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, NP, NC = X.shape
LEN, NE, NFEN = 24, 32, 4000          # 4000 tranches suffisent pour des taux de base
print("=" * 84); print(" SONDE AUC — que mesure le 0,9996 ?"); print("=" * 84)
print("  corpus : %d ticks x %d entites x %d colonnes" % (T, NP, NC), flush=True)

# --- on reconstruit des tranches par la MEME recette que monde.py (entites presentes partout)
rng = np.random.default_rng(11)
OBS = np.zeros((NFEN, LEN, NE, 8), np.float32)
MSQ = np.zeros((NFEN, LEN, NE), np.float32)
n = ess = 0
while n < NFEN and ess < NFEN * 8:
    ess += 1
    t = int(rng.integers(0, T - LEN - 1))
    pres = np.asarray(P[t:t + LEN])                      # (LEN, NP)
    ok = np.where(pres.all(0))[0]
    if len(ok) < 4: continue
    sel = ok if len(ok) <= NE else rng.choice(ok, NE, replace=False)
    OBS[n, :, :len(sel)] = np.asarray(X[t:t + LEN, sel, :8])
    MSQ[n, :, :len(sel)] = 1.0
    n += 1
OBS, MSQ = OBS[:n], MSQ[:n]
print("  %d tranches, %d entites suivies en moyenne sur %d emplacements"
      % (n, MSQ[:, 0].sum(1).mean(), NE), flush=True)

viv = OBS[..., 3]                                        # colonne « vivant »
m = MSQ[:, 1:] * MSQ[:, :-1]                             # le masque de monde.py

def auc(p, y):
    o = np.argsort(p, kind="stable"); y = y[o]
    pos = y.sum(); neg = len(y) - pos
    if pos == 0 or neg == 0: return float("nan")
    return float((np.arange(1, len(y) + 1)[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

print("\n─── S1 · LE REMPLISSAGE ───")
tot = m.size
print("  emplacements evalues par monde.py : %d" % tot)
print("  dont REELS (masque=1)             : %d   soit %.1f %%" % (m.sum(), 100 * m.sum() / tot))
print("  dont REMPLISSAGE (masque=0)       : %d   soit %.1f %%" % (tot - m.sum(), 100 * (tot - m.sum()) / tot))
print("  -> le remplissage entre dans l AUC avec (prediction 0, cible 0) : negatifs parfaits.")

print("\n─── S2 · LA CIBLE ───")
cible_monde = ((1.0 - viv[:, 1:]) * m).ravel()           # celle de monde.py
reels = m.ravel() > 0
mort_k = (1.0 - viv[:, :-1]).ravel()[reels]
mort_k1 = (1.0 - viv[:, 1:]).ravel()[reels]
transition = ((viv[:, :-1] > 0.5) & (viv[:, 1:] < 0.5)).ravel()[reels].astype(float)
print("  cible de monde.py, sur TOUT le tenseur : taux de positifs %.4f %%" % (100 * cible_monde.mean()))
print("  sur les emplacements REELS :")
print("     deja mort au pas k        %.2f %%" % (100 * mort_k.mean()))
print("     mort au pas k+1           %.2f %%" % (100 * mort_k1.mean()))
print("     ⭐ MEURT ENTRE k ET k+1    %.4f %%   <- la vraie cible" % (100 * transition.mean()))
print("  -> %.1f %% des « morts en k+1 » etaient DEJA morts en k." % (100 * (mort_k1.sum() - transition.sum()) / max(mort_k1.sum(), 1)))

print("\n─── S3 · LE TEMOIN TRIVIAL (zero parametre) ───")
print("  temoin = « il sera mort en k+1 s il etait mort en k ». Aucun apprentissage.")
# a) sur la cible ET le perimetre de monde.py (remplissage compris)
p_triv = ((1.0 - viv[:, :-1]) * m).ravel()
print("  a) cible ET perimetre de monde.py .................. AUC %.4f" % auc(p_triv, (cible_monde > 0.5).astype(int)))
# b) meme cible, mais SANS le remplissage
print("  b) meme cible, emplacements REELS seulement ........ AUC %.4f" % auc(mort_k, (mort_k1 > 0.5).astype(int)))
# c) la VRAIE cible : la transition
print("  c) VRAIE cible (meurt entre k et k+1), reels ....... AUC %.4f" % auc(mort_k, transition.astype(int)))
print("\n  LECTURE :")
print("   · si (a) est deja ~0,999, le 0,9996 du modele ne demontre RIEN — un recopiage sans")
print("     parametre l atteint, et l AUC mesure la forme du tenseur plus que le monde ;")
print("   · (c) est la seule des trois qui pose la question interessante.")
