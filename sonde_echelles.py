#!/usr/bin/env python3
"""sonde_echelles — LE TROU QUE FABLE A LAISSE DANS MES SONDES.

« Aucune entree constante » ne verifie PAS les ECHELLES. Une entree a queue lourde ou
d amplitude etrangere peut ecraser l apprentissage precoce — et le brouilleur preserve ce
defaut a l identique, donc le bras C ne le controle PAS.

On mesure, sur les MEMES etats, la distribution de chaque entree :
  · les 12 nombres de la reference (le bras A)
  · les 8 prix du controle positif (le bras P)
  · les 6 canaux du raster (le bras B)
Le critere est simple et il est celui du reseau : ce que voit un `Linear` suivi d un `tanh`,
c est l amplitude. Une entree dont l ecart-type est 10x plus petit que les autres n a pas
10x moins de poids : elle a un gradient 10x plus faible AU DEPART, et le depart decide.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import prix_des_actions
from raster import raster, CANAUX_DEFAUT, K_DEFAUT, SPAN_DEFAUT

COLS = ["apx", "apy", "dgx", "dgy", "vivant", "pente", "dcover", "los", "nd",
        "?9", "?10", "?11"]

print("=" * 78); print(" SONDE ECHELLES"); print("=" * 78)
# on echantillonne le long d une trajectoire, pas au reset : c est la que le reseau vit
etats = []
e = B.monde(256, 11); o = e.reset()
for t in range(30):
    etats.append((o.detach(), prix_des_actions(e), raster(e, K=K_DEFAUT, span=SPAN_DEFAUT)))
    o, _, done, _ = e.step(B.frontal(e, t), auto_reset=False)
    if bool(done.all()): break
O = torch.cat([x[0] for x in etats], 0)
P = torch.cat([x[1] for x in etats], 0)
R = torch.cat([x[2] for x in etats], 0)

def ligne(nom, v):
    v = v.reshape(-1).float()
    q = torch.quantile(v[torch.randperm(v.numel())[:200000]],
                       torch.tensor([0.01, 0.5, 0.99], device=v.device))
    print("  %-14s moy %+8.4f  e-t %8.4f  p01 %+8.4f  med %+8.4f  p99 %+8.4f  |max| %8.2f"
          % (nom, v.mean(), v.std(), q[0], q[1], q[2], v.abs().max()))
    return float(v.std())

print("\n─── LES 12 NOMBRES (bras A, la reference qui GAGNE) ───")
ets_a = [ligne(COLS[i] if i < len(COLS) else "col%d" % i, O[..., i]) for i in range(O.shape[-1])]

print("\n─── LES 8 PRIX (bras P, le controle positif qui PERD) ───")
ets_p = [ligne("prix cap %d" % i, P[..., i]) for i in range(8)]

print("\n─── LES 6 CANAUX DU RASTER (bras B) ───")
ets_r = [ligne(CANAUX_DEFAUT[i], R[:, :, i]) for i in range(len(CANAUX_DEFAUT))]

print("\n─── LE VERDICT D ECHELLE ───")
import statistics
ma = statistics.median([x for x in ets_a if x > 1e-9])
mp = statistics.median(ets_p); mr = statistics.median(ets_r)
print("  ecart-type MEDIAN — les 12 nombres %.4f | les 8 prix %.4f | le raster %.4f" % (ma, mp, mr))
print("  rapport prix / nombres  : %.2f   %s" % (mp / ma, "OK" if 0.2 < mp / ma < 5 else "⚠️ HORS BANDE"))
print("  rapport raster / nombres: %.2f   %s" % (mr / ma, "OK" if 0.2 < mr / ma < 5 else "⚠️ HORS BANDE"))
print("\n  Ce que voit la PREMIERE couche : la part de la variance totale d entree")
va = float((O ** 2).mean()) * O.shape[-1]
vp = float((P ** 2).mean()) * 8
vr = float((R ** 2).mean()) * R[0, 0].numel()
print("    bras P : les 12 nombres portent %.1f %% de l energie, les 8 prix %.1f %%"
      % (100 * va / (va + vp), 100 * vp / (va + vp)))
print("    bras B : les 12 nombres portent %.1f %% de l energie, le raster %.1f %%"
      % (100 * va / (va + vr), 100 * vr / (va + vr)))
print()
