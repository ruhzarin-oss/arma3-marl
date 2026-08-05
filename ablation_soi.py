#!/usr/bin/env python3
"""ablation_soi.py — D'OU VIENNENT LES 6,3 POINTS que coute la transferabilite ?

R1 a echoue : le predicteur GEOMETRIE (0,7178) perd 6,3 points quand on le reduit a ce que
la sandbox sait calculer (0,6549). Mon critere disait alors « le predicteur s'appuyait sur
des entrees intransferables ». Reste a savoir LESQUELLES — et la reponse change tout :

  · si l'ecart vient des COORDONNEES ABSOLUES, le predicteur a appris « on meurt plus a tel
    endroit d'Altis ». C'est vrai sur ce corpus, sans aucune valeur ailleurs, et la variante
    transferable est alors la seule HONNETE — pas une version degradee.
  · si l'ecart vient de l'AZIMUT ou de la SUPPRESSION, ce sont des grandeurs physiques que
    la sandbox pourrait fournir, et il faut les lui donner.

ON MESURE, on ne suppose pas. Une colonne de SOI rendue a la fois, a partir de la variante
transferable. ⟨SOI = [x/1000, y/1000, z/100, azimut/360, posture/3, suppression]⟩
"""
import sys, math, time
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
te = est_test

def auc(s, y):
    s = np.asarray(s, float); y = np.asarray(y, float)
    n1 = y.sum(); n0 = len(y) - n1
    r = np.empty(len(s)); r[np.argsort(s)] = np.arange(len(s))
    return float((r[y > 0.5].sum() - n1*(n1-1)/2) / (n1*n0))

class Risque(nn.Module):
    def __init__(s, ce, cs, h=96):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(ce, h), nn.ReLU(), nn.Linear(h, h))
        s.q = nn.Linear(cs, h)
        s.out = nn.Sequential(nn.Linear(cs+h, h), nn.ReLU(), nn.Linear(h, 1))
    def forward(s, soi, enn, msk):
        z = s.enc(enn)
        a = (z * s.q(soi).unsqueeze(1)).sum(-1) / math.sqrt(z.shape[-1])
        a = torch.softmax(a.masked_fill(msk < 0.5, -1e9), -1).unsqueeze(-1)
        return s.out(torch.cat([soi, (z*a).sum(1)], -1)).squeeze(-1)

def entraine(S_, E_, graine=0, iters=800):
    torch.manual_seed(graine); np.random.seed(graine)
    m = Risque(E_.shape[-1], S_.shape[-1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), 2e-3)
    tr = np.where(~te)[0]
    S = torch.tensor(S_, device=dev); E = torch.tensor(E_, device=dev)
    M = torch.tensor(MASQ, device=dev); Yt = torch.tensor(Y, device=dev)
    pos = float(Y[tr].mean()); w = torch.tensor((1-pos)/max(pos,1e-6), device=dev)
    for _ in range(iters):
        b = torch.tensor(np.random.choice(tr, 4096), device=dev)
        l = nn.functional.binary_cross_entropy_with_logits(m(S[b],E[b],M[b]), Yt[b], pos_weight=w)
        opt.zero_grad(); l.backward(); opt.step()
    with torch.no_grad():
        idx = np.where(te)[0]; o = []
        for i in range(0, len(idx), 65536):
            b = torch.tensor(idx[i:i+65536], device=dev)
            o.append(m(S[b],E[b],M[b]).cpu().numpy())
    return auc(np.concatenate(o), Y[te])

E_tr = ENN[:, :, [3,4,5]].copy()          # d, angle sur moi, angle sur lui
NOMS = ['x absolu', 'y absolu', 'altitude', 'azimut du soldat', 'posture', 'suppression']
TRANSFERABLE = [False, False, False, True, True, False]

base = entraine(SOI[:, [4]].copy(), E_tr)
print(f"\n  variante TRANSFERABLE (posture seule) ......... AUC {base:.4f}", flush=True)
print(f"  {'colonne rendue':22s} {'AUC':>8s} {'gain':>8s}   transferable ?")
print("  " + "-"*58)
gains = []
for j, nom in enumerate(NOMS):
    if j == 4: continue                    # deja dans la base
    S_ = SOI[:, [4, j]].copy()
    a = entraine(S_, E_tr, graine=j+1)
    gains.append((nom, a - base, TRANSFERABLE[j]))
    print(f"  {nom:22s} {a:8.4f} {a-base:+8.4f}   "
          f"{'OUI' if TRANSFERABLE[j] else 'non'}", flush=True)

# et le nombre de defenseurs, que la sandbox connait parfaitement
S_n = np.stack([SOI[:, 4], MASQ.sum(1)/12.0], -1).astype(np.float32)
a_n = entraine(S_n, E_tr, graine=20)
print(f"  {'nombre de defenseurs':22s} {a_n:8.4f} {a_n-base:+8.4f}   OUI", flush=True)

print("\n" + "="*66)
tr_gain = max([g for _, g, t in gains if t] + [a_n - base])
non_tr = max([g for _, g, t in gains if not t] + [0.0])
print(f"  meilleur gain TRANSFERABLE ....... {tr_gain:+.4f}")
print(f"  meilleur gain NON transferable ... {non_tr:+.4f}")
print("="*66)
if non_tr > tr_gain + 0.01:
    print("  L'ECART VIENT D'ENTREES INTRANSFERABLES. Le predicteur s'appuyait sur des")
    print("  particularites du corpus — position sur la carte, altitude, suppression subie —")
    print("  qui n'existent pas dans la sandbox et ne DOIVENT pas y exister.")
    print("  La variante transferable n'est donc pas degradee : c'est la seule HONNETE.")
else:
    print("  L'ECART VIENT D'ENTREES QUE LA SANDBOX POURRAIT FOURNIR. Il faut les lui")
    print("  donner avant de substituer quoi que ce soit.")
