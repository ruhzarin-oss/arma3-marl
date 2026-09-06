#!/usr/bin/env python3
"""jointure — RENDRE LA MORT VISIBLE. La cible n existait pas ; on la construit.

ETABLI (DIAGNOSTIC_MONDE.md, febc6d2c7eb27bb0) : une entite ne meurt JAMAIS dans
`noeuds.npy` — 0 passage vivant->mort a identifiant constant sur 13,6 M de paires ; `vivant`
change pour 3 entites sur 19 309. Les 10 196 morts vivent dans `morts.npy` (instant, victime,
tueur, code).

CE QUE FAIT CE FICHIER : joindre l evenement sur la ligne de temps des noeuds, puis MESURER
la cible obtenue et ses temoins triviaux — avant qu un seul modele ne la voie.

⚠️ Le probleme d unites : la colonne 0 de `morts.npy` va de 87,97 a 37 979,80 pour 173 338
ticks. Ce ne sont donc PAS des indices de tick. On identifie l unite AVANT de joindre —
sinon on joindrait sur un decalage, ce qui est exactement la faute qu on vient de diagnostiquer.
"""
import numpy as np, json
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
M = np.load(f'{D}/morts.npy'); meta = json.load(open(f'{D}/meta.json'))
T, NP, NC = X.shape
print("=" * 88); print(" JOINTURE — rendre la mort visible"); print("=" * 88)

print("\n─── 1. L UNITE DE LA COLONNE 0 DE morts.npy ───")
t0, t1 = float(M[:, 0].min()), float(M[:, 0].max())
print("  morts.npy col 0 : %.2f a %.2f      noeuds : %d ticks" % (t0, t1, T))
print("  rapport ticks / etendue = %.4f" % (T / (t1 - t0)))
for nom, f in (("secondes (tick = 0,2 s)", 5.0), ("secondes (tick = 1 s)", 1.0),
               ("deja des ticks", 1.0 / max(T / (t1 - t0), 1e-9))):
    print("    si %-26s -> couvre %8.0f ticks  %s"
          % (nom, (t1 - t0) * f, "PLAUSIBLE" if 0.5 * T <= (t1 - t0) * f <= 1.5 * T else ""))

print("\n─── 2. LES IDENTIFIANTS SE RECOUVRENT-ILS ? ───")
rng = np.random.default_rng(1); ids_noeuds = set()
for _ in range(8):
    t = int(rng.integers(0, T - 500))
    b = np.asarray(X[t:t + 500, :, 0]); p = np.asarray(P[t:t + 500, :]) > 0.5
    ids_noeuds |= set(np.unique(b[p]).tolist())
vict = set(np.unique(M[:, 1][M[:, 1] >= 0]).tolist())
tue = set(np.unique(M[:, 2][M[:, 2] >= 0]).tolist())
print("  identifiants vus dans les noeuds (echantillon) : %d" % len(ids_noeuds))
print("  victimes distinctes dans morts.npy ............ %d   dont %d se retrouvent dans les noeuds (%.1f %%)"
      % (len(vict), len(vict & ids_noeuds), 100 * len(vict & ids_noeuds) / max(len(vict), 1)))
print("  tueurs distincts .............................. %d   dont %d (%.1f %%)"
      % (len(tue), len(tue & ids_noeuds), 100 * len(tue & ids_noeuds) / max(len(tue), 1)))
print("  -> %s" % ("les identifiants sont COMPATIBLES, la jointure est possible"
                   if len(vict & ids_noeuds) > 0.3 * len(vict) else
                   "⛔ LES IDENTIFIANTS NE SE RECOUVRENT PAS — la jointure est impossible en l etat"))

print("\n─── 3. UNE VICTIME EST-ELLE ETIQUETEE `vivant` AVANT SA MORT ? ───")
# si les victimes sont deja etiquetees mortes partout, l etiquette encode le SORT FINAL,
# pas l etat courant — et alors elle FUITE la reponse.
ech = list(vict & ids_noeuds)[:400]
if ech:
    vu_v = vu_m = 0
    for _ in range(10):
        t = int(rng.integers(0, T - 500))
        b = np.asarray(X[t:t + 500, :, :]); p = np.asarray(P[t:t + 500, :]) > 0.5
        idb, vb = b[..., 0], b[..., 4]
        msk = p & np.isin(idb, ech)
        vu_v += int((vb[msk] > 0.5).sum()); vu_m += int((vb[msk] < 0.5).sum())
    tot = vu_v + vu_m
    print("  lignes d entites qui MEURENT un jour : %d vivantes, %d mortes (%.1f %% vivantes)"
          % (vu_v, vu_m, 100 * vu_v / max(tot, 1)))
    print("  -> %s" % ("l etiquette suit le temps : une victime est vivante AVANT, morte APRES."
                       if 0.15 < vu_v / max(tot, 1) < 0.85 else
                       "⚠️ l etiquette encode le SORT FINAL, pas l etat courant : elle FUITE la reponse."))
else:
    print("  aucun identifiant commun a echantillonner.")
