#!/usr/bin/env python3
"""cout_filtre — LE QUATRIEME DEFAUT, ET IL EST DANS MA REPARATION ⟨Fable, 26/08⟩.

« Selectionner sur `id` constant est juste, mais c est une SELECTION : les hommes qui MEURENT
sont ceux dont la trace casse, donc le filtre risque d appauvrir exactement la classe rare
que la cible transition doit apprendre. »

On mesure donc, AVANT de reparer : ce que le filtre garde, et surtout combien de POSITIFS il
laisse. A 0,0113 % de taux de base, une AUC sans son n de positifs n est pas un chiffre.
"""
import numpy as np
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T = X.shape[0]; LEN, NE, NFEN = 24, 32, 6000
rng = np.random.default_rng(11)
ids, viv, n, ess = [], [], 0, 0
while n < NFEN and ess < NFEN * 8:
    ess += 1
    t = int(rng.integers(0, T - LEN - 1)); pres = np.asarray(P[t:t + LEN])
    ok = np.where(pres.all(0))[0]
    if len(ok) < 4: continue
    sel = ok if len(ok) <= NE else rng.choice(ok, NE, replace=False)
    b = np.asarray(X[t:t + LEN, sel, :])
    ids.append(b[..., 0].reshape(LEN, -1).T); viv.append(b[..., 4].reshape(LEN, -1).T); n += 1
ids = np.concatenate(ids); viv = np.concatenate(viv)
stable = (ids == ids[:, :1]).all(1)                      # identifiant constant sur TOUTE la trace
def trans(v):
    return ((v[:, :-1] > 0.5) & (v[:, 1:] < 0.5))
print("=" * 84); print(" COUT DU FILTRE « identifiant constant » — appauvrit-il la classe rare ?")
print("=" * 84)
print("  traces echantillonnees .................. %d" % len(ids))
print("  traces GARDEES par le filtre ............ %d   soit %.1f %%" % (stable.sum(), 100 * stable.mean()))
ta, tf = trans(viv), trans(viv[stable])
print("\n  %-34s %12s %12s" % ("", "AVANT filtre", "APRES filtre"))
print("  %-34s %12d %12d" % ("pas (paires k, k+1)", ta.size, tf.size))
print("  %-34s %12d %12d" % ("TRANSITIONS positives (n)", ta.sum(), tf.sum()))
print("  %-34s %11.4f %% %11.4f %%" % ("taux de base", 100 * ta.mean(), 100 * tf.mean()))
if ta.sum() > 0:
    print("\n  -> le filtre conserve %.1f %% des pas mais seulement %.1f %% des POSITIFS."
          % (100 * tf.size / ta.size, 100 * tf.sum() / ta.sum()))
    r = (tf.sum() / max(tf.size, 1)) / max(ta.sum() / max(ta.size, 1), 1e-12)
    print("     enrichissement de la classe rare : x%.2f   %s"
          % (r, "IL L APPAUVRIT — Fable a raison" if r < 0.8 else
                "il l enrichit" if r > 1.25 else "neutre"))
print("\n  ⚠️ toute AUC sur la transition se publie desormais AVEC son n de positifs.")
