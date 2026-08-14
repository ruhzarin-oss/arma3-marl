import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
NOMS = ["apx/S","apy/S","dgx","dgy","alive","slope","dcover","los","nd","p_deb","p_acc","p_cou"]
Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
G, pol = [], charger(B.DEV)
def rec(o, t):
    G.append(o.reshape(-1, o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l, v = pol(o); return l.argmax(-1), None, None
B.jouer(B.monde(64, 101), rec)
G = np.concatenate(G).astype(np.float64)
gg = np.repeat(np.arange(len(G)//8), 8)[:len(G)]
def parcol(X, g):
    return np.median(np.stack([X[g==k].std(0) for k in np.unique(g) if (g==k).sum()>1]), 0)
eg, ea = parcol(G[:len(gg)], gg), parcol(A, pas)
print("  ETALEMENT ENTRE CAMARADES, colonne par colonne (mediane sur les pas)\n")
print(f"  {'colonne':<9}{'gymnase':>10}{'arma':>10}{'manque':>10}")
for i, n in enumerate(NOMS):
    print(f"  {n:<9}{eg[i]:>10.4f}{ea[i]:>10.4f}{eg[i]-ea[i]:>10.4f}")
d = eg - ea
o = np.argsort(-d)[:3]
print(f"\n  total   {eg.mean():>10.4f}{ea.mean():>10.4f}{d.mean():>10.4f}")
print(f"\n  les trois plus gros manques : " + ", ".join(f"{NOMS[i]} ({d[i]:+.4f})" for i in o))
print(f"  part du deficit qu ils portent : {100*d[o].sum()/d.sum():.0f} %")
