import sys, glob, numpy as np, torch, pathlib
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
L = "/mnt/data/harmattan-sandbox/logs/live20"
E = [np.load(f, allow_pickle=True)["obs18"][:, COLS].astype(np.float64)
     for f in sorted(glob.glob(f"{L}/ep_*.npz"))]
AA = np.concatenate(E)
G, pol = [], charger(B.DEV)
def rec(o,t):
    G.append(o.reshape(-1,o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l,v=pol(o); return l.argmax(-1),None,None
B.jouer(B.monde(64,101), rec)
G = np.concatenate(G).astype(np.float64)
k = 6   # dcover
print("─── dcover : la colonne qui fait tomber la porte ───")
for nom, X in [("GYMNASE", G[:,k]), ("ARMA (20 episodes)", AA[:,k])]:
    print(f"  {nom:<20} 1% {np.percentile(X,1):.3f}  50% {np.percentile(X,50):.3f}  99% {np.percentile(X,99):.3f}  moy {X.mean():.3f}")
print(f"\n  plage gymnase [1%;99%] = [{np.percentile(G[:,k],1):.3f} ; {np.percentile(G[:,k],99):.3f}]")
print(f"  mediane Arma = {np.percentile(AA[:,k],50):.3f}  →  " +
      ("DANS" if np.percentile(G[:,k],1) <= np.percentile(AA[:,k],50) <= np.percentile(G[:,k],99) else "HORS"))
print(f"\n  part des decisions d Arma au-dessus du 99e centile du gymnase : {100*(AA[:,k] > np.percentile(G[:,k],99)).mean():.1f} %")
print("\n─── par episode : combien ont leur mediane dcover hors plage ? ───")
gl, gh = np.percentile(G[:,k],1), np.percentile(G[:,k],99)
n = sum(1 for e in E if not (gl <= np.percentile(e[:,k],50) <= gh))
print(f"  {n}/{len(E)} episodes")
print(f"  medianes par episode : {', '.join(f'{np.percentile(e[:,k],50):.2f}' for e in E)}")
