#!/usr/bin/env python3
"""filtre_par_paire — LE FILTRE SE POSE SUR LA PAIRE, PAS SUR LA FENETRE.

Mon filtre exigeait l identifiant constant sur les 24 pas : il supprimait 100 % des morts,
parce qu une trace ou personne ne meurt est precisement une trace dont la place n a pas ete
liberee. Mais une transition ne demande qu UNE PAIRE propre : id[k] == id[k+1].
On mesure les deux, et on garde celui qui conserve la classe rare.
"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T = X.shape[0]; LEN, NE, NFEN = 24, 32, 6000
rng = np.random.default_rng(11)
I, V, S = [], [], []
n = ess = 0
while n < NFEN and ess < NFEN * 8:
    ess += 1
    t = int(rng.integers(0, T - LEN - 1)); pres = np.asarray(P[t:t + LEN])
    ok = np.where(pres.all(0))[0]
    if len(ok) < 4: continue
    sel = ok if len(ok) <= NE else rng.choice(ok, NE, replace=False)
    b = np.asarray(X[t:t + LEN, sel, :])
    I.append(b[..., 0].reshape(LEN, -1).T); V.append(b[..., 4].reshape(LEN, -1).T)
    S.append(b[..., 9].reshape(LEN, -1).T)          # suppression, pour le temoin
    n += 1
I = np.concatenate(I); V = np.concatenate(V); S = np.concatenate(S)
paire_propre = I[:, :-1] == I[:, 1:]                       # LE BON FILTRE
fen_propre = (I == I[:, :1]).all(1)[:, None].repeat(I.shape[1] - 1, 1)   # l ancien
trans = (V[:, :-1] > 0.5) & (V[:, 1:] < 0.5)

print("=" * 86); print(" LE FILTRE SE POSE SUR LA PAIRE, PAS SUR LA FENETRE"); print("=" * 86)
print("  %-32s %12s %12s %12s" % ("", "SANS filtre", "par FENETRE", "par PAIRE"))
for nom, msk in (("pas gardes", None), ("transitions positives (n)", None)):
    pass
tot = trans.size
print("  %-32s %12d %12d %12d" % ("pas gardes", tot, fen_propre.sum(), paire_propre.sum()))
print("  %-32s %12d %12d %12d" % ("TRANSITIONS positives (n)", trans.sum(),
                                  (trans & fen_propre).sum(), (trans & paire_propre).sum()))
print("  %-32s %11.4f %% %11.4f %% %11.4f %%" % ("taux de base",
      100 * trans.mean(), 100 * (trans & fen_propre).sum() / max(fen_propre.sum(), 1),
      100 * (trans & paire_propre).sum() / max(paire_propre.sum(), 1)))
print("  %-32s %12s %11.1f %% %11.1f %%" % ("positifs conserves", "100 %",
      100 * (trans & fen_propre).sum() / max(trans.sum(), 1),
      100 * (trans & paire_propre).sum() / max(trans.sum(), 1)))

def auc(p, y):
    o = np.argsort(p, kind="stable"); y = y[o]
    pos = y.sum(); neg = len(y) - pos
    if pos == 0 or neg == 0: return float("nan"), int(pos)
    return float((np.arange(1, len(y) + 1)[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)), int(pos)

print("\n─── LE BARREAU, RECALCULE SUR LE BANC REPARE (filtre par PAIRE) ───")
m = paire_propre
for nom, score in (("« il etait mort en k »", (V[:, :-1] < 0.5).astype(float)),
                   ("« suppression subie en k »", S[:, :-1]),
                   ("hasard (temoin nul)", np.random.default_rng(3).random(m.shape))):
    a, npos = auc(score[m], trans[m].astype(int))
    print("  %-30s AUC %.4f   sur n = %d positifs" % (nom, a, npos))
print("\n  ⚠️ une AUC sur la transition ne se publie JAMAIS sans son n de positifs.")
print("     Ici la classe rare pese %d cas : c est le nombre qui borne tout ce qu on pourra dire."
      % (trans & paire_propre).sum())
