"""Les hommes survivent et n arrivent pas. Avancent-ils AUSSI VITE qu au gymnase ?
Grandeur : metres gagnes vers l objectif PAR PAS. Elle est directement comparable."""
import sys, glob, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
S_NORM = 200.0   # terr_R : les colonnes 0/1 sont apx/S, apy/S

# ─── ARMA : distance a l objectif par pas, moyenne des hommes
vit_a = []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True)
    A = Z["obs18"][:, COLS]; pas = np.asarray(Z["pas"])
    d = [np.sqrt(A[pas==p,0]**2 + A[pas==p,1]**2).mean()*S_NORM for p in np.unique(pas)]
    if len(d) > 5: vit_a.append((d[0]-d[-1])/(len(d)-1))

# ─── GYMNASE : la meme chose, avec la meme politique
pol = charger(B.DEV); D = []
def rec(o,t):
    with torch.no_grad(): l,v = pol(o)
    return l.argmax(-1), None, None
e = B.monde(64, 101)
o = e.reset(); prem = None; dern = None; n = 0
for t in range(60):
    d = torch.sqrt(e.apx**2 + e.apy**2).mean(1)
    if prem is None: prem = d.clone()
    dern = d.clone(); n = t+1
    with torch.no_grad(): l, v = pol(e._obs())
    o, _, done, info = e.step(l.argmax(-1), auto_reset=False)
    if bool(done.all()): break
vit_g = ((prem - dern)/max(n-1,1)).cpu().numpy()

print(f"  METRES GAGNES VERS L OBJECTIF, PAR PAS\n")
print(f"  {'':<10}{'mediane':>10}{'moyenne':>10}{'min':>9}{'max':>9}")
print(f"  {'GYMNASE':<10}{np.median(vit_g):>10.2f}{vit_g.mean():>10.2f}{vit_g.min():>9.2f}{vit_g.max():>9.2f}")
print(f"  {'ARMA':<10}{np.median(vit_a):>10.2f}{np.mean(vit_a):>10.2f}{np.min(vit_a):>9.2f}{np.max(vit_a):>9.2f}")
r = np.median(vit_g)/max(np.median(vit_a),1e-9)
print(f"\n  rapport gymnase/Arma : x{r:.1f}")
print(f"\n  a la vitesse d Arma, couvrir 170 m demande {170/max(np.median(vit_a),1e-9):.0f} pas.")
print(f"  a la vitesse du gymnase : {170/max(np.median(vit_g),1e-9):.0f} pas.   Le banc en donne 60.")
