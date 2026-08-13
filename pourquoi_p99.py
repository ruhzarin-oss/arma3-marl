#!/usr/bin/env python3
"""pourquoi_p99 — LA CAUSE, PAS UN COEFFICIENT.

Le depot disait : « un quantile hors de +-15 % -> on cherche pourquoi au lieu d ajuster un
coefficient ». Voici pourquoi.

La pente d un point du gymnase = relief_de_la_carte x forme_locale. En tirant le relief DANS la
distribution des pentes de Stratis, j ai applique la variation DEUX FOIS : celle de la carte, et
celle interne a chaque carte qui existait deja. Les variances s ajoutent, la queue haute enfle.

On mesure les deux morceaux separement, et on voit s ils peuvent se recomposer.
"""
import sys, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

S = np.load("/home/younes/arma3-marl/pentes_stratis.npy")
S = np.sort(S)
qS = lambda p: float(S[int(p * (len(S) - 1))])

def quantiles(v):
    v = sorted(v); q = lambda p: v[int(p * (len(v) - 1))]
    return q(0.01), q(0.5), q(0.99)

cfg = dict(MONDE_ARMA); cfg["relief_stratis"] = False
e = AssaultTerrain(num_envs=256, seed=5, device="cuda:0", max_steps=10, **cfg)
W = e.reset().reshape(-1, 12)[:, 5].tolist()
w1, w50, w99 = quantiles(W)
print(f"\n  LA FORME INTERNE d une carte (relief CONSTANT = {e.relief})")
print(f"    p01 {w1:.3f}   median {w50:.3f}   p99 {w99:.3f}")
print(f"    etalement multiplicatif : x{w1/w50:.2f} .. x{w99/w50:.2f}")
print(f"\n  STRATIS, point a point")
print(f"    p01 {qS(0.01):.3f}   median {qS(0.5):.3f}   p99 {qS(0.99):.3f}")
print(f"    etalement multiplicatif : x{qS(0.01)/qS(0.5):.2f} .. x{qS(0.99)/qS(0.5):.2f}")
print(f"\n  LECTURE")
print(f"    La forme interne du gymnase s etale deja de x{w1/w50:.2f} a x{w99/w50:.2f} ;")
print(f"    Stratis de x{qS(0.01)/qS(0.5):.2f} a x{qS(0.99)/qS(0.5):.2f}.")
print( "    La variete existait DEJA a l interieur de chaque carte. En tirant le relief dans")
print( "    la distribution de Stratis, je l ai appliquee une SECONDE fois.")
print(f"\n  CE QUE DIRAIT UN SIMPLE FACTEUR D ECHELLE (relief x {qS(0.5)/w50:.3f})")
k = qS(0.5) / w50
for nom, g, c in (("p01", w1*k, qS(0.01)), ("median", w50*k, qS(0.5)), ("p99", w99*k, qS(0.99))):
    if c < 1e-6:
        print(f"    {nom:<8}{g:>8.3f} contre {c:>7.3f}   ecart absolu {abs(g-c):.3f}")
    else:
        print(f"    {nom:<8}{g:>8.3f} contre {c:>7.3f}   {100*(g-c)/c:+.0f} %")
print("\n  -> le facteur seul redresse la mediane et la queue haute, mais laisse un PLANCHER")
print("     que Stratis n a pas : la carte a de VRAIES plaines, le bruit lisse du gymnase non.")
print("     Ce n est pas un coefficient qui manque, c est une FORME de terrain.")
