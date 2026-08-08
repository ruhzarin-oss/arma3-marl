#!/usr/bin/env python3
"""couverture.py — L EMETTEUR MESURE-T-IL LA VUE DE FACON REGULIERE ?

L anomalie : « vu maintenant » vaut 12,0 %, « vu dans 10 s » vaut 0,6 %. Vingt fois moins,
dans un monde ou l exposition est reputee ULTRA-PERSISTANTE. Ce n est pas un resultat, c est
un symptome.

Deux causes possibles, et la mesure les separe :
  (a) L EMETTEUR ne mesure qu une PARTIE des aretes a chaque passage — HMT_VMAX borne le
      nombre de lineIntersectsSurfaces par soldat et par tick, et le reste sort a -1
      (« non mesure », a ne pas lire comme « pas de vue »). Si la couverture varie d un
      releve a l autre, comparer deux instants compare deux echantillons differents.
  (b) MA TABLE d identifiants perd des hommes entre les deux instants.

CE QU ON MESURE :
  1. la part d aretes MESUREES par tick, et sa variabilite ;
  2. la persistance REELLE de l etat « vu », mesuree UNIQUEMENT sur les paires dont la vue
     est mesuree AUX DEUX instants — la seule comparaison qui ait un sens ;
  3. combien d hommes survivent a ma table entre t et t+DELTA.

Si (a) : le test d avenir doit se restreindre aux paires mesurees des deux cotes, et son
resultat d hier ne vaut rien.
"""
import math, numpy as np
from collections import defaultdict

DELTA_S, DEMI_CONE = 10.0, 35.0
D = '/mnt/data/corpus/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy')
TPS = np.load(f'{D}/temps.npy')
T, N, _ = X.shape

par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    par_tick[int(t)].append((int(a), int(b), v, mes))
ticks = np.array(sorted(par_tick.keys()))
dt = float(np.median(np.diff(TPS[ticks])))
saut = max(1, int(round(DELTA_S / max(dt, 1e-6))))

print(f"\n  {len(ticks)} ticks porteurs d aretes · pas median {dt:.2f} s · DELTA {saut} releves")

# ---- 1. la couverture de la mesure de vue
parts = []
for ti in ticks[::37][:400]:
    l = par_tick[int(ti)]
    if l:
        parts.append(sum(1 for *_, m in l if m > 0.5) / len(l))
parts = np.array(parts)
print("\n" + "=" * 74)
print("  1. PART D ARETES DONT LA VUE EST MESUREE, par tick")
print("  " + "-" * 72)
print(f"     mediane {np.median(parts):.1%} · min {parts.min():.1%} · max {parts.max():.1%}"
      f" · ecart-type {parts.std():.3f}")


def table(ti):
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    return {int(xt[j, 0]): (xt[j, 1], xt[j, 2], xt[j, 7])
            for j in range(N) if pt[j] and xt[j, 0] > 0 and xt[j, 4] > 0.5}


def vu_mesure(ti, T_):
    """(vu, mesure) par soldat : mesure = au moins une arete mesuree le concernant."""
    vu, mes = set(), set()
    for a, b, v, m in par_tick[ti]:
        if a not in T_ or b not in T_:
            continue
        if m > 0.5:
            mes.add(a)
        if m > 0.5 and v > 0.5:
            xa, ya, _ = T_[a]
            xb, yb, ab = T_[b]
            gis = math.degrees(math.atan2(xa - xb, ya - yb)) % 360
            if abs(((gis - ab + 180) % 360) - 180) < DEMI_CONE:
                vu.add(a)
    return vu, mes


print("\n" + "=" * 74)
print("  2. PERSISTANCE REELLE, sur les hommes MESURES AUX DEUX INSTANTS")
print("  " + "-" * 72)
n_paires = n_survit = 0
n_vu_p = n_vu_pf = n_sur_p = n_sur_vf = 0
for i in range(0, len(ticks) - saut, 53):
    ti, tf = int(ticks[i]), int(ticks[i + saut])
    Tp, Tf = table(ti), table(tf)
    vp, mp = vu_mesure(ti, Tp)
    vf, mf = vu_mesure(tf, Tf)
    communs = (mp & mf) & set(Tp) & set(Tf)
    n_paires += len(mp)
    n_survit += len(communs)
    for u in communs:
        if u in vp:
            n_vu_p += 1
            n_vu_pf += (u in vf)
        else:
            n_sur_p += 1
            n_sur_vf += (u in vf)
print(f"     hommes mesures a t : {n_paires} · encore mesures a t+{DELTA_S:.0f}s :"
      f" {n_survit} ({n_survit/max(n_paires,1):.1%})")
if n_vu_p:
    print(f"     VU a t     -> encore vu a t+{DELTA_S:.0f}s : {n_vu_pf}/{n_vu_p}"
          f" = {n_vu_pf/n_vu_p:.1%}   <- la persistance REELLE")
if n_sur_p:
    print(f"     SUR a t    -> vu a t+{DELTA_S:.0f}s     : {n_sur_vf}/{n_sur_p}"
          f" = {n_sur_vf/n_sur_p:.1%}   <- la vraie TRANSITION")

print("\n" + "=" * 74)
if n_survit / max(n_paires, 1) < 0.5:
    print("  CAUSE (a) CONFIRMEE : plus de la moitie des hommes ne sont PAS mesures aux deux")
    print("  instants. Comparer t et t+10 s comparait deux ECHANTILLONS DIFFERENTS, pas deux")
    print("  etats du meme monde. Le test d avenir d hier NE VAUT RIEN et se refait sur les")
    print("  seules paires mesurees des deux cotes.")
elif n_vu_p and n_vu_pf / n_vu_p > 0.5:
    print("  LA PERSISTANCE EST REELLE et la couverture suffisante : l anomalie venait d")
    print("  ailleurs — a chercher dans ma construction, pas dans l emetteur.")
else:
    print("  COUVERTURE SUFFISANTE mais persistance FAIBLE : l etat « vu » est plus volatil")
    print("  que le dossier ne le disait. C est un fait sur le monde, a verser.")
print("  " + "=" * 72)
