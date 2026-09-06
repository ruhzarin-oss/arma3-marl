#!/usr/bin/env python3
"""famille_temoins — LE BARREAU. Maximum d une famille FERMEE, deposee avant tout calcul.

Depot : DEPOT_TEMOINS.md, hachage 85c8f481a72026ea, ecrit AVANT d avoir ouvert aretes.npy.
Cible : la TRANSITION vivant->mort, suivie par IDENTIFIANT a travers les places.

⚠️ T4 (« tir dirige sur lui dans les N derniers pas ») N EST PAS CALCULABLE : les aretes
   portent (tick, source, cible, knowsAbout, vue, mesuree) — elles n encodent PAS qui tire
   sur qui. Je le DECLARE au lieu de lui substituer autre chose en douce ; la regle du depot
   l exige. La famille effective compte donc quatre traits, et le barreau est leur maximum.
"""
import numpy as np, json, hashlib, time
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy')
T = X.shape[0]
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_TEMOINS.md', 'rb').read()).hexdigest()[:16]
R = json.load(open('/mnt/data/reparation.json'))
print("=" * 96); print(" LE BARREAU — maximum de la famille deposee (%s)" % H); print("=" * 96, flush=True)

# ─── index des aretes : (tick, cible) -> vue, knowsAbout   [col 5 = mesuree]
ok = AR[:, 5] > 0.5
tk = AR[ok, 0].astype(np.int64); cib = AR[ok, 2].astype(np.int64)
ka = AR[ok, 3]; vue = AR[ok, 4]
cle = tk * 100000 + cib
o = np.argsort(cle, kind="stable"); cle, ka, vue = cle[o], ka[o], vue[o]
print("  aretes MESUREES indexees : %d sur %d" % (ok.sum(), len(AR)), flush=True)

def lire(cles):
    """max de knowsAbout et de vue pour chaque (tick, cible) demande."""
    i = np.searchsorted(cle, cles, side="left"); j = np.searchsorted(cle, cles, side="right")
    k_out = np.zeros(len(cles), np.float32); v_out = np.zeros(len(cles), np.float32)
    for n in range(len(cles)):
        if j[n] > i[n]:
            k_out[n] = ka[i[n]:j[n]].max(); v_out[n] = vue[i[n]:j[n]].max()
    return k_out, v_out

bornes = np.linspace(0, T, 21).astype(int)
def recolter(blocs, max_bloc=3):
    L = []
    for b in blocs[:max_bloc]:
        t0, t1 = bornes[b], min(bornes[b] + 6000, bornes[b + 1])
        A = np.asarray(X[t0:t1]); pr = np.asarray(P[t0:t1]) > 0.5
        idb = A[..., ID]; ids = np.unique(idb[pr])
        for u in ids[:: max(1, len(ids) // 250)]:
            m = pr & (idb == u)
            if m.sum() < 15: continue
            tt, pl = np.nonzero(m); o2 = np.argsort(tt); tt, pl = tt[o2], pl[o2]
            gu, gi = np.unique(tt, return_index=True); tt, pl = tt[gi], pl[gi]
            a = A[tt, pl, :]
            if len(a) < 3: continue
            v = a[:, VIV]
            trans = (v[:-1] > 0.5) & (v[1:] < 0.5)
            # les traits au pas k, uniquement quand l homme est VIVANT en k
            vivant_k = v[:-1] > 0.5
            dep = np.r_[0.0, np.linalg.norm(np.diff(a[:, [XX, YY]], axis=0), axis=1)][:-1]
            k_ka, k_vue = lire(np.sort((tt[:-1] + t0) * 100000 + int(u)))
            L.append(dict(y=trans[vivant_k], supp=a[:-1, SUPP][vivant_k],
                          vue=k_vue[vivant_k], ka=k_ka[vivant_k],
                          bouge=dep[vivant_k], t=tt[:-1][vivant_k] + t0, pl=pl[:-1][vivant_k],
                          x=a[:-1, XX][vivant_k], yy=a[:-1, YY][vivant_k], camp=a[:-1, CAMP][vivant_k]))
    return L

t0 = time.time(); L = recolter(R["blocs_ecart"])
print("  traces recoltees sur les blocs TENUS A L ECART : %d  (%.0f s)" % (len(L), time.time() - t0), flush=True)
cat = lambda k: np.concatenate([d[k] for d in L])
y = cat("y").astype(int)
print("  pas evalues %d   TRANSITIONS n = %d   taux de base %.4f %%"
      % (len(y), y.sum(), 100 * y.mean()), flush=True)

def auc(p, y):
    o = np.argsort(p, kind="stable"); yy = y[o]
    pos = yy.sum(); neg = len(yy) - pos
    if pos == 0 or neg == 0: return float("nan")
    return float((np.arange(1, len(yy) + 1)[yy == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

print("\n─── LA FAMILLE, CHACUN SUR LA MEME CIBLE ───")
TEM = {
    "T1 suppression subie": cat("supp"),
    "T2a est-vu (arete vue=1)": cat("vue"),
    "T2b knowsAbout dirige vers lui": cat("ka"),
    "T5 immobile (moins on bouge, plus on meurt)": -cat("bouge"),
    "T5' en mouvement (l inverse)": cat("bouge"),
    "PLANCHER hasard": np.random.default_rng(3).random(len(y)),
}
res = {}
for n, p in TEM.items():
    a = auc(p, y); res[n] = a
    print("  %-46s AUC %.4f" % (n, a))
print("  %-46s %s" % ("T3 distance au plus proche ennemi", "non calcule ici (couteux, a faire)"))
print("  %-46s %s" % ("T4 tir dirige sur lui", "⛔ NON CALCULABLE — les aretes n encodent pas qui tire"))
vrais = {k: v for k, v in res.items() if not k.startswith("PLANCHER")}
best = max(vrais, key=vrais.get)
print("\n  ⭐ LE BARREAU = %.4f   (`%s`)   sur n = %d positifs" % (vrais[best], best, y.sum()))
print("  plancher hasard %.4f" % res["PLANCHER hasard"])
print("\n  Tout modele du monde se publie contre CE maximum, jamais contre le temoin qui l arrange.")
json.dump({"hachage": H, "n_positifs": int(y.sum()), "n_pas": int(len(y)),
           "temoins": res, "barreau": vrais[best], "barreau_nom": best},
          open('/mnt/data/barreau.json', 'w'), indent=1)
