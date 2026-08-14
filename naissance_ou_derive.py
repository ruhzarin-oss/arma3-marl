"""L etalement que j ai pris pour une porte est-il une propriete de la NAISSANCE
ou un RESULTAT de l episode ? Si le gymnase nait aussi serre qu Arma et s ecarte
ensuite, ma porte mesurait une consequence et la designait comme une cause."""
import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
GS, pol = [], charger(B.DEV)
def rec(o, t):
    GS.append((t, o.reshape(-1, o.shape[-1]).cpu().numpy()))
    with torch.no_grad(): l, v = pol(o); return l.argmax(-1), None, None
B.jouer(B.monde(64, 101), rec)
def et(X, g): return np.median([X[g==k].std(0).mean() for k in np.unique(g) if (g==k).sum()>1])
# gymnase : un env = 8 hommes consecutifs
def etg(o): 
    g = np.repeat(np.arange(len(o)//8), 8)[:len(o)]; return et(o[:len(g)], g)
print("  ETALEMENT DU GYMNASE, PAS PAR PAS")
print(f"  {'pas':>5}{'etalement':>12}")
for t, o in GS[:1] + GS[1:6] + GS[10:11] + GS[20:21] + GS[40:41]:
    print(f"  {t:>5}{etg(o):>12.4f}")
n0 = etg(GS[0][1]); nm = np.median([etg(o) for _, o in GS])
a0 = et(A[pas == pas.min()], np.zeros((pas == pas.min()).sum()) * 0 + 1) if False else A[pas==pas.min()].std(0).mean()
am = et(A, pas)
print(f"\n  GYMNASE  a la NAISSANCE {n0:.4f}   ·  mediane sur l episode {nm:.4f}   ->  x{nm/max(n0,1e-9):.1f}")
print(f"  ARMA     a la NAISSANCE {a0:.4f}   ·  mediane sur l episode {am:.4f}   ->  x{am/max(a0,1e-9):.1f}")
print("\n─── LA LECTURE ───")
if abs(a0 - n0) < 0.25 * max(n0, 1e-9):
    print(f"  ⇒ Les deux NAISSENT pareil ({a0:.4f} contre {n0:.4f}). La greffe a fait son travail.")
    print(f"     L ecart vient de la DERIVE : le gymnase s ecarte x{nm/max(n0,1e-9):.1f}, Arma x{am/max(a0,1e-9):.1f}.")
    print("     Ma porte mesurait un RESULTAT et le designait comme une cause. Elle est mal posee.")
else:
    print(f"  ⇒ Les naissances different encore ({a0:.4f} contre {n0:.4f}) : la greffe est incomplete.")
