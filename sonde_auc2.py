#!/usr/bin/env python3
"""sonde_auc2 — CE QUE MESURE REELLEMENT LE 0,9996. Etabli, pas deduit.

`meta.json` donne onze champs : id x y z vivant camp tir azimut posture suppression neuf.
`monde.py` prend X[...,:8] et les commente « x,y,z,vivant,camp,tir,azimut,suppression ».
IL A OUBLIE `id`. Tout est decale d un cran. On le DEMONTRE ici, colonne par colonne.
"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, NP, NC = X.shape
CH = ["id","x","y","z","vivant","camp","tir","azimut","posture","suppression","neuf"]
LEN, NE, NFEN = 24, 32, 4000
print("=" * 86); print(" SONDE AUC 2 — le banc `monde.py` est DECALE D UNE COLONNE"); print("=" * 86)

rng = np.random.default_rng(11)
OBS = np.zeros((NFEN, LEN, NE, 8), np.float32); MSQ = np.zeros((NFEN, LEN, NE), np.float32)
BRUT = np.zeros((NFEN, LEN, NE, 11), np.float32)
n = ess = 0
while n < NFEN and ess < NFEN * 8:
    ess += 1
    t = int(rng.integers(0, T - LEN - 1)); pres = np.asarray(P[t:t + LEN])
    ok = np.where(pres.all(0))[0]
    if len(ok) < 4: continue
    sel = ok if len(ok) <= NE else rng.choice(ok, NE, replace=False)
    b = np.asarray(X[t:t + LEN, sel, :])
    BRUT[n, :, :len(sel)] = b; OBS[n, :, :len(sel)] = b[..., :8]; MSQ[n, :, :len(sel)] = 1.0
    n += 1
OBS, MSQ, BRUT = OBS[:n], MSQ[:n], BRUT[:n]
m = (MSQ[:, 1:] * MSQ[:, :-1]) > 0
print("  %d tranches, %d entites suivies\n" % (n, MSQ[:, 0].sum(1).mean()))

print("─── A · LA PREUVE DU DECALAGE : ce que `monde.py` croit lire, et ce qu il lit ───")
print("  %-3s %-14s %-14s %12s %12s %8s" % ("i", "croit lire", "LIT VRAIMENT", "min", "max", "n val."))
for i in range(8):
    v = OBS[..., i][MSQ > 0]
    print("  %-3d %-14s %-14s %12.2f %12.2f %8d"
          % (i, ["x","y","z","vivant","camp","tir","azimut","suppression"][i], CH[i],
             v.min(), v.max(), len(np.unique(np.round(v, 3)))))

print("\n─── B · LA TETE DE MORT EST ENTRAINEE SUR L ALTITUDE ───")
z = BRUT[..., 3]; viv = BRUT[..., 4]
print("  colonne 3 lue par monde.py = `%s` : min %.1f max %.1f, %d valeurs distinctes -> PAS binaire"
      % (CH[3], z[MSQ > 0].min(), z[MSQ > 0].max(), len(np.unique(np.round(z[MSQ > 0], 2)))))
print("  colonne 4 = `%s`            : moyenne %.4f, valeurs %s -> LA VRAIE cible"
      % (CH[4], viv[MSQ > 0].mean(), np.unique(viv[MSQ > 0])))

def auc(p, y):
    o = np.argsort(p, kind="stable"); y = y[o]
    pos = y.sum(); neg = len(y) - pos
    if pos == 0 or neg == 0: return float("nan")
    return float((np.arange(1, len(y) + 1)[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

vk, vk1 = viv[:, :-1][m], viv[:, 1:][m]
zk = z[:, :-1][m]
mort_k1 = (vk1 < 0.5).astype(int)
trans = ((vk > 0.5) & (vk1 < 0.5)).astype(int)
print("\n  taux de base sur les emplacements reels :")
print("     deja mort au pas k .............. %6.2f %%" % (100 * (vk < 0.5).mean()))
print("     mort au pas k+1 ................. %6.2f %%" % (100 * mort_k1.mean()))
print("     ⭐ MEURT ENTRE k ET k+1 .......... %6.4f %%" % (100 * trans.mean()))
print("     part des morts en k+1 deja morts en k : %.2f %%"
      % (100 * (mort_k1.sum() - trans.sum()) / max(mort_k1.sum(), 1)))

print("\n─── C · LE TEMOIN TRIVIAL, SUR CHAQUE CIBLE (zero parametre) ───")
print("  1) cible de monde.py (1 - ALTITUDE), score = altitude en k ......... AUC %.4f"
      % auc(-zk, (z[:, 1:][m] < np.median(zk)).astype(int)))
print("  2) VRAIE cible « est mort en k+1 », score = mort en k .............. AUC %.4f"
      % auc((vk < 0.5).astype(float), mort_k1))
print("  3) ⭐ VRAIE cible « MEURT entre k et k+1 », score = mort en k ....... AUC %.4f"
      % auc((vk < 0.5).astype(float), trans))
print("  4) ⭐ meme cible, score = suppression subie en k .................... AUC %.4f"
      % auc(BRUT[..., 9][:, :-1][m], trans))

print("\n─── D · L ERREUR DE POSITION PORTE SUR (id, x), PAS (x, y) ───")
d = OBS[:, 1:, :, :2] - OBS[:, :-1, :, :2]
print("  composante 0 (`%s`) : ecart-type %.6f  -> %s" % (CH[0], d[..., 0][m].std(),
      "CONSTANTE, la moitie de la cible vaut zero" if d[..., 0][m].std() < 1e-6 else "varie"))
print("  composante 1 (`%s`)  : ecart-type %.4f" % (CH[1], d[..., 1][m].std()))
dv = BRUT[:, 1:, :, 1:3] - BRUT[:, :-1, :, 1:3]
print("  la VRAIE cible (x,y) : ecart-type %.4f et %.4f" % (dv[..., 0][m].std(), dv[..., 1][m].std()))
print("  -> l erreur publiee est la moitie d une erreur : un des deux axes est identiquement nul,")
print("     ce qui divise par deux `err` ET `err_pers` et les rend indiscernables.")
