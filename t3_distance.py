#!/usr/bin/env python3
"""t3_distance — LE TRAIT MANQUANT DE LA FAMILLE. Sans lui, le barreau n est pas le maximum
de la famille DEPOSEE, c est le maximum de ce que j ai eu le temps de calculer.

T3 = distance au plus proche ENNEMI au pas k. « Ennemi » = camp different (colonne 5).
Meme cible, memes blocs TENUS A L ECART, meme n de positifs que le calcul precedent.

On en profite pour verser a la PORTE MOYENNE sa premiere anomalie : `etre vu` ne rend que
0,5666 ici, alors que le dossier annonce « etre vu tue 2x plus fort » sur 563 000 observations.
On mesure donc aussi le RAPPORT DE TAUX (pas l AUC) : le taux de mort des VUS contre celui
des NON-VUS. C est la grandeur que la fiche annonce, et elle n est pas la meme qu une AUC.
"""
import numpy as np, json, hashlib, time
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy')
T = X.shape[0]
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
R = json.load(open('/mnt/data/reparation.json'))
B = json.load(open('/mnt/data/barreau.json'))
print("=" * 96); print(" T3 — LE TRAIT MANQUANT, ET LE RAPPORT DE TAUX D ETRE VU"); print("=" * 96, flush=True)

ok = AR[:, 5] > 0.5
cle = AR[ok, 0].astype(np.int64) * 100000 + AR[ok, 2].astype(np.int64)
ka, vue = AR[ok, 3], AR[ok, 4]
o = np.argsort(cle, kind="stable"); cle, ka, vue = cle[o], ka[o], vue[o]

bornes = np.linspace(0, T, 21).astype(int)
Y, SU, VU, KA, DI, BO = [], [], [], [], [], []
t0 = time.time()
for b in R["blocs_ecart"][:3]:
    ta, tb = bornes[b], min(bornes[b] + 6000, bornes[b + 1])
    A = np.asarray(X[ta:tb]); pr = np.asarray(P[ta:tb]) > 0.5
    idb = A[..., ID]
    # ─── T3 : pour CHAQUE instant, la distance de chacun au plus proche d un AUTRE camp
    px, py, cp = A[..., XX], A[..., YY], A[..., CAMP]
    dmin = np.full(px.shape, np.inf, np.float32)
    for c in (0.0, 1.0):
        moi = pr & (cp == c); adv = pr & (cp != c)
        for t in range(px.shape[0]):
            ia = np.nonzero(adv[t])[0]; im = np.nonzero(moi[t])[0]
            if len(ia) == 0 or len(im) == 0: continue
            d2 = (px[t, im][:, None] - px[t, ia][None]) ** 2 + (py[t, im][:, None] - py[t, ia][None]) ** 2
            dmin[t, im] = np.sqrt(d2.min(1))
    ids = np.unique(idb[pr])
    for u in ids[:: max(1, len(ids) // 250)]:
        m = pr & (idb == u)
        if m.sum() < 15: continue
        tt, pl = np.nonzero(m); s = np.argsort(tt); tt, pl = tt[s], pl[s]
        gu, gi = np.unique(tt, return_index=True); tt, pl = tt[gi], pl[gi]
        a = A[tt, pl, :]
        if len(a) < 3: continue
        v = a[:, VIV]; trans = (v[:-1] > 0.5) & (v[1:] < 0.5); vk = v[:-1] > 0.5
        dep = np.r_[0.0, np.linalg.norm(np.diff(a[:, [XX, YY]], axis=0), axis=1)][:-1]
        cl = np.sort((tt[:-1] + ta) * 100000 + int(u))
        i = np.searchsorted(cle, cl, "left"); j = np.searchsorted(cle, cl, "right")
        kk = np.zeros(len(cl), np.float32); vv = np.zeros(len(cl), np.float32)
        for n in range(len(cl)):
            if j[n] > i[n]: kk[n] = ka[i[n]:j[n]].max(); vv[n] = vue[i[n]:j[n]].max()
        dd = dmin[tt[:-1], pl[:-1]]
        Y.append(trans[vk]); SU.append(a[:-1, SUPP][vk]); VU.append(vv[vk]); KA.append(kk[vk])
        DI.append(dd[vk]); BO.append(dep[vk])
cc = lambda L: np.concatenate(L)
y = cc(Y).astype(int); su, vu2, ka2, di, bo = cc(SU), cc(VU), cc(KA), cc(DI), cc(BO)
fini = np.isfinite(di)
print("  pas evalues %d  |  TRANSITIONS n = %d  |  %.1f %% ont un ennemi identifiable  (%.0f s)"
      % (len(y), y.sum(), 100 * fini.mean(), time.time() - t0), flush=True)

def auc(p, yy):
    o = np.argsort(p, kind="stable"); z = yy[o]
    pos = z.sum(); neg = len(z) - pos
    if pos == 0 or neg == 0: return float("nan")
    return float((np.arange(1, len(z) + 1)[z == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

print("\n─── LA FAMILLE COMPLETE (T3 inclus) ───")
fam = {"T1 suppression subie": su, "T2a est-vu": vu2, "T2b knowsAbout": ka2,
       "T3 proximite de l ennemi (1/distance)": np.where(fini, -di, -1e9), "T5 immobile": -bo}
for n, p in fam.items():
    print("  %-40s AUC %.4f" % (n, auc(p, y)))
best = max(fam, key=lambda k: auc(fam[k], y))
print("\n  ⭐ BARREAU COMPLET = %.4f  (`%s`)  sur n = %d positifs" % (auc(fam[best], y), best, y.sum()))
print("     (avant T3, il valait %.4f)" % B["barreau"])

print("\n─── L ANOMALIE POUR LA PORTE MOYENNE : le RAPPORT DE TAUX d etre vu ───")
print("  la fiche annonce « etre vu tue 2x plus fort » — c est un RAPPORT DE TAUX, pas une AUC.")
for nom, msk in (("VU (arete vue=1)", vu2 > 0.5), ("knowsAbout > 1", ka2 > 1.0),
                 ("SUPPRIME (supp > 0)", su > 1e-6)):
    a, b_ = y[msk], y[~msk]
    if len(a) and len(b_) and b_.mean() > 0:
        print("  %-22s taux %.4f %%  contre  %.4f %%  ->  RAPPORT x%.2f   (n vus = %d)"
              % (nom, 100 * a.mean(), 100 * b_.mean(), a.mean() / b_.mean(), msk.sum()))
json.dump({"barreau_complet": auc(fam[best], y), "nom": best, "n_positifs": int(y.sum()),
           "famille": {k: auc(v, y) for k, v in fam.items()}},
          open('/mnt/data/barreau_complet.json', 'w'), indent=1)
