"""conjoint — les 12 colonnes sont chacune DANS sa plage. Le sont-elles ENSEMBLE ?

CONTROLE POSITIF ⟨regle 16⟩ : la mesure est une distance de Mahalanobis au gymnase.
Par construction, les points DU GYMNASE doivent y etre proches. Si le gymnase lui-meme
sort, l instrument est faux et on ne lit rien.
"""
import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B

Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
A = Z["obs18"][:, COLS]
pas = np.asarray(Z["pas"])

G, pol = [], charger(B.DEV)
def rec(o, t):
    G.append(o.reshape(-1, o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l, v = pol(o)
    return l.argmax(-1), None, None
B.jouer(B.monde(64, 101), rec)
G = np.concatenate(G).astype(np.float64)
A = A.astype(np.float64)

mu = G.mean(0)
S = np.cov(G, rowvar=False) + 1e-6 * np.eye(G.shape[1])
Si = np.linalg.inv(S)
def maha(X): 
    d = X - mu
    return np.sqrt(np.einsum("ij,jk,ik->i", d, Si, d))
mg, ma = maha(G), maha(A)

print(f"  gymnase {len(G)} points · Arma {len(A)} points · {G.shape[1]} dimensions\n")
print("─── DISTANCE DE MAHALANOBIS AU GYMNASE ───")
for nom, v in [("GYMNASE (controle positif)", mg), ("ARMA", ma)]:
    print(f"  {nom:<28} 50% {np.percentile(v,50):7.2f}   99% {np.percentile(v,99):7.2f}   max {v.max():7.2f}")
seuil = np.percentile(mg, 99)
print(f"\n  seuil = 99e centile du gymnase : {seuil:.2f}")
print(f"  points d Arma au-dela             : {100*(ma>seuil).mean():.1f} %")
print(f"  mediane d Arma en centile gymnase : {100*(mg < np.median(ma)).mean():.2f} %")

print("\n─── L ETALEMENT DES HUIT HOMMES (ecart-type entre camarades, meme pas) ───")
def etal(X, grp):
    return np.array([X[grp == g].std(0).mean() for g in np.unique(grp) if (grp == g).sum() > 1])
gg = np.repeat(np.arange(len(G)//8), 8)[:len(G)]
eg, ea = etal(G[:len(gg)], gg), etal(A, pas)
print(f"  GYMNASE  mediane {np.median(eg):.4f}")
print(f"  ARMA     mediane {np.median(ea):.4f}   →  {np.median(eg)/max(np.median(ea),1e-9):.1f}x plus SERRE")

print("\n─── LA LECTURE ───")
if np.percentile(mg, 99) < 1e-9:
    print("  ⛔ instrument faux : le gymnase lui-meme est degenere.")
elif (ma > seuil).mean() > 0.5:
    print("  ⇒ Les colonnes sont chacune dans sa plage et CONJOINTEMENT hors distribution.")
    print("     La faute n est plus le SITE : c est la CONFIGURATION que le banc impose.")
else:
    print("  ⇒ Arma tombe dans la distribution conjointe du gymnase. Le gel vient d AILLEURS.")
