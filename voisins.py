"""voisins — LA QUESTION QUI RESTE. Arma tombe dans la distribution conjointe du gymnase,
et la politique s y fige quand meme. Alors : que fait-elle sur les points DU GYMNASE qui
ressemblent le plus a ceux d Arma ?

Si le gymnase se fige AUSSI la-bas, le gel n est pas une panne : c est la reponse apprise
a cette configuration, et c est le BANC qui n a jamais reproduit les SITUATIONS du gymnase,
seulement ses marges.
"""
import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B

Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
A = Z["obs18"][:, COLS].astype(np.float64)
G, pol = [], charger(B.DEV)
def rec(o, t):
    G.append(o.reshape(-1, o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l, v = pol(o)
    return l.argmax(-1), None, None
B.jouer(B.monde(64, 101), rec)
G = np.concatenate(G).astype(np.float64)

with torch.no_grad():
    ag = pol(torch.tensor(G, dtype=torch.float32, device=B.DEV))[0].argmax(-1).cpu().numpy()
    aa = pol(torch.tensor(A, dtype=torch.float32, device=B.DEV))[0].argmax(-1).cpu().numpy()

sd = G.std(0) + 1e-9
d = np.sqrt((((G[:, None, :] - A[None, :, :]) / sd) ** 2).sum(-1))   # (gym, arma)
dmin = d.min(1)

def h(a, nom):
    u, c = np.unique(a, return_counts=True)
    print(f"  {nom:<34} {dict(zip(u.tolist(), c.tolist()))}")
    print(f"  {'':<34} dominante {100*c.max()/len(a):.1f} %  ·  {len(u)}/10 actions")

print(f"  gymnase {len(G)} · Arma {len(A)} · distance normalisee par ecart-type\n")
print("─── QUE FAIT LA POLITIQUE, ET OU ───")
h(ag, "GYMNASE entier")
h(aa, "ARMA")
for k in (200, 1000):
    idx = np.argsort(dmin)[:k]
    h(ag[idx], f"GYMNASE — {k} plus proches d Arma")

print(f"\n  distance du plus proche voisin gymnase a un point d Arma :")
print(f"    mediane {np.median(dmin):.2f}  ·  1er centile {np.percentile(dmin,1):.2f}")
print(f"  distance typique ENTRE points du gymnase : {np.median(np.sqrt((((G[:500,None,:]-G[None,:500,:])/sd)**2).sum(-1))):.2f}")

print("\n─── LA LECTURE ───")
idx = np.argsort(dmin)[:200]
u, c = np.unique(ag[idx], return_counts=True)
dom = 100 * c.max() / len(idx)
if dom > 70:
    print(f"  ⇒ Le gymnase SE FIGE AUSSI la-bas ({dom:.1f} % sur une action).")
    print("     Le gel n est PAS une panne : c est la reponse apprise a cette configuration.")
    print("     La faute est que le BANC ne reproduit que les MARGES, jamais les SITUATIONS.")
else:
    print(f"  ⇒ Le gymnase VARIE la-bas ({dom:.1f} % au plus). Arma se fige la ou le gymnase choisit :")
    print("     il reste un ecart que ni les marges ni la distribution conjointe n expliquent.")
