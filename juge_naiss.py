import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
act = np.asarray(Z["actions"]).reshape(-1)
G, pol = [], charger(B.DEV)
def rec(o, t):
    G.append(o.reshape(-1, o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l, v = pol(o)
    return l.argmax(-1), None, None
B.jouer(B.monde(64, 101), rec)
G = np.concatenate(G).astype(np.float64)
gg = np.repeat(np.arange(len(G)//8), 8)[:len(G)]
et = lambda X, g: np.array([X[g==k].std(0).mean() for k in np.unique(g) if (g==k).sum() > 1])
eg, ea = np.median(et(G[:len(gg)], gg)), np.median(et(A, pas))

p0 = pas == pas.min()
vy = A[p0, 1].std()
print(f"  {len(A)} decisions sur {len(np.unique(pas))} pas\n")
print("─── CONTROLE POSITIF : les huit hommes partagent-ils encore un apy identique ? ───")
print(f"  ecart-type de apy/S au premier pas : {vy:.4f}")
print("  " + ("✓ PASSE — la greffe a mordu" if vy > 1e-6 else "⛔ TOMBE — variance NULLE, rien ne se lit"))
if vy <= 1e-6: raise SystemExit
print("\n─── LA PORTE, SUR LE MECANISME ───")
print(f"  etalement : {ea:.4f}   (avant 0,069 · gymnase {eg:.4f} · porte 0,12)")
print("  " + ("✓ PASSE" if ea > 0.12 else f"⛔ TOMBE — {ea:.4f} sous la porte"))
print("\n─── RAPPORTE, NON JUGE : les actions ───")
u, c = np.unique(act, return_counts=True)
print(f"  ARMA {dict(zip(u.tolist(), c.tolist()))}   dominante {100*c.max()/len(act):.1f} %  ·  {len(u)}/10")
print(f"  (avant l etalement : 100,0 % sur une seule action)")
print(f"\n  survie : {len(np.unique(pas))} pas   (le chantier suivant, non traite ici)")
