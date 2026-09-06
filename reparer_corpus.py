#!/usr/bin/env python3
"""reparer_corpus — PISTE A. Indexer par IDENTIFIANT, et calculer la famille de temoins.

Criteres deposes AVANT tout calcul : DEPOT_TEMOINS.md, hachage 85c8f481a72026ea.
Le barreau est le MAXIMUM de la famille, publie avec son n de positifs.

CE QUI EST REPARE, ETABLI LE 26/08 :
 · `monde.py` suivait des PLACES ; 93,5 % des entites changent de place au cours de leur vie,
   donc 0 transition vivant->mort etait visible. En suivant l IDENTIFIANT : 771 transitions
   sur 2 043 entites, 0 transition inverse (l etiquette est monotone).
 · `monde.py` prenait X[...,:8] en oubliant la colonne `id` : tout etait decale d un cran,
   sa « tete de mort » etait entrainee sur l ALTITUDE.
Colonnes vraies : 0=id 1=x 2=y 3=z 4=vivant 5=camp 6=tir 7=azimut 8=posture 9=suppression 10=neuf
"""
import numpy as np, json, hashlib, time
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, NP, NC = X.shape
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_TEMOINS.md', 'rb').read()).hexdigest()[:16]
print("=" * 92); print(" RÉPARATION — indexer par IDENTIFIANT.  temoins deposes : %s" % H); print("=" * 92, flush=True)

# ─── BLOCS TENUS A L ECART : on decoupe le temps en blocs et on en reserve, jamais melanges.
NB_BLOCS = 20
bornes = np.linspace(0, T, NB_BLOCS + 1).astype(int)
rng = np.random.default_rng(11)
ordre = rng.permutation(NB_BLOCS)
BL_ETUDE = sorted(ordre[:14].tolist()); BL_ECART = sorted(ordre[14:].tolist())
print("  %d blocs de temps ; %d a l ETUDE, %d TENUS A L ECART (jamais melanges)"
      % (NB_BLOCS, len(BL_ETUDE), len(BL_ECART)), flush=True)

def traces(blocs, max_bloc=3):
    """Suit chaque identifiant A TRAVERS LES PLACES, dans les blocs demandes."""
    out = []
    for b in blocs[:max_bloc]:
        t0, t1 = bornes[b], min(bornes[b] + 6000, bornes[b + 1])
        A = np.asarray(X[t0:t1]); pr = np.asarray(P[t0:t1]) > 0.5
        idb = A[..., ID]
        ids = np.unique(idb[pr])
        for u in ids[:: max(1, len(ids) // 250)]:
            m = pr & (idb == u)
            if m.sum() < 15: continue
            tt, pl = np.nonzero(m); o = np.argsort(tt); tt, pl = tt[o], pl[o]
            # un seul echantillon par instant (si l id figure a deux places, on garde la 1re)
            gu, gi = np.unique(tt, return_index=True)
            tt, pl = tt[gi], pl[gi]
            out.append((A[tt, pl, :], tt + t0, u))
    return out

t0 = time.time()
TR = traces(BL_ETUDE)
print("  %d traces suivies par identifiant  (%.0f s)" % (len(TR), time.time() - t0), flush=True)
np.save('/mnt/data/traces_etude.npy', np.array([1]))   # marque de passage
print("\n─── CE QUE LA REPARATION REND ───")
n_trans = n_pas = 0
for a, tt, u in TR:
    v = a[:, VIV]
    n_trans += int(((v[:-1] > 0.5) & (v[1:] < 0.5)).sum()); n_pas += len(v) - 1
print("  paires (k, k+1) suivies ......... %d" % n_pas)
print("  TRANSITIONS vivant -> mort ...... %d   taux de base %.4f %%" % (n_trans, 100 * n_trans / max(n_pas, 1)))
print("  -> %s" % ("la cible EXISTE et elle est calculable" if n_trans > 30 else
                   "⛔ trop peu de positifs pour un barreau : elargir les blocs"))
json.dump({"hachage_temoins": H, "blocs_etude": BL_ETUDE, "blocs_ecart": BL_ECART,
           "n_traces": len(TR), "n_pas": n_pas, "n_transitions": n_trans},
          open('/mnt/data/reparation.json', 'w'), indent=1)
print("\n  ecrit dans /mnt/data/reparation.json")
