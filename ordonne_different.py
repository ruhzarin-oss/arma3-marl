#!/usr/bin/env python3
"""ordonne_different.py — LE RISQUE APPRIS ET expo ORDONNENT-ILS DIFFEREMMENT ?

⟨Fable, 05/08 : « applique ta propre regle avant le run : verifier sur dix trajectoires
 existantes que le predicteur et expo ordonnent DIFFEREMMENT les etats traverses — sinon
 le remplacement ne peut rien changer. »⟩

C'est la regle nee de l'echec du champ de risque : mesurer que le remplacement PEUT agir,
avant de payer une demi-heure de GPU pour le decouvrir.

CE QUI EST DEJA ETABLI
  expo, la fonction de cout actuelle .......... AUC 0,5005   le hasard pur
  risque appris, variante TRANSFERABLE ........ AUC 0,6549
  et l'ablation montre que l'ecart avec la variante « geometrie » (0,7178) vient a 92 %
  de la SUPPRESSION SUBIE — « je suis deja sous le feu » —, une quasi-tautologie que la
  sandbox n'a pas et ne doit pas avoir.

LE TEST. Sur les trajectoires reellement produites par l'agent, on classe les etats
traverses selon expo, puis selon le risque appris, et on compare les deux classements.

  correlation de rang ELEVEE  -> les deux disent la meme chose, substituer ne changera rien
  correlation FAIBLE ou NEGATIVE -> le remplacement peut agir

CRITERE, ecrit avant : |rho| < 0,5 pour que la substitution ait un sens.
"""
import sys, math, json
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
te = est_test

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

# ---------------------------------------------------------------- entrainer et SAUVEGARDER
E_tr = ENN[:, :, [3,4,5]].copy(); S_tr = SOI[:, [4]].copy()
torch.manual_seed(0); np.random.seed(0)
m = Risque(3, 1).to(dev)
opt = torch.optim.Adam(m.parameters(), 2e-3)
tr = np.where(~te)[0]
S = torch.tensor(S_tr, device=dev); E = torch.tensor(E_tr, device=dev)
M = torch.tensor(MASQ, device=dev); Yt = torch.tensor(Y, device=dev)
pos = float(Y[tr].mean()); w = torch.tensor((1-pos)/max(pos,1e-6), device=dev)
for _ in range(800):
    b = torch.tensor(np.random.choice(tr, 4096), device=dev)
    l = nn.functional.binary_cross_entropy_with_logits(m(S[b],E[b],M[b]), Yt[b], pos_weight=w)
    opt.zero_grad(); l.backward(); opt.step()

def auc(s, y):
    s = np.asarray(s,float); y = np.asarray(y,float); n1=y.sum(); n0=len(y)-n1
    r = np.empty(len(s)); r[np.argsort(s)] = np.arange(len(s))
    return float((r[y>0.5].sum() - n1*(n1-1)/2)/(n1*n0))
with torch.no_grad():
    idx = np.where(te)[0]; o=[]
    for i in range(0,len(idx),65536):
        b = torch.tensor(idx[i:i+65536], device=dev); o.append(m(S[b],E[b],M[b]).cpu().numpy())
a_C = auc(np.concatenate(o), Y[te])
torch.save({'etat': m.state_dict(), 'ce': 3, 'cs': 1, 'auc': a_C},
           '/mnt/data/corpus/risque_geo.pt')
print(f"\n  risque appris (transferable) : AUC {a_C:.4f}  -> ecrit risque_geo.pt", flush=True)

# ---------------------------------------------------------------- les etats traverses
CH, SEUIL, PENTE = 35.0, 120.0, 12.0
def expo_np(p, defs):
    v = p[:, None, :] - defs[None, :, :2]
    d = np.maximum(np.linalg.norm(v, axis=-1), 1.0)
    gis = np.degrees(np.arctan2(v[...,0], v[...,1])) % 360
    ec = np.abs((gis - defs[None,:,2] + 180) % 360 - 180)
    dans = 1/(1+np.exp(-np.clip((CH-ec)*1.2, -60, 60)))
    base = 0.45*(1-np.clip(d/400,0,1))
    return ((base + (1-base)*dans) * (1-np.clip(d/450,0,1))).max(axis=1), d, ec

src_t = json.load(open('/mnt/data/corpus/trajectoires_agent150_sanschamp.json'))[:20]
EX, RI = [], []
for c in src_t:
    defs = np.array(c['defenseurs'], float)
    p = np.array(c['agent'], float)
    e, d, ec = expo_np(p, defs)
    K = 12
    n = min(len(defs), K)
    Ee = np.zeros((len(p), K, 3), np.float32); Mm = np.zeros((len(p), K), np.float32)
    # meme convention que le corpus : les defenseurs classes, d/400, angles/180
    ordre = np.argsort(ec, axis=1)[:, :n]
    for i in range(len(p)):
        for j, k in enumerate(ordre[i]):
            # a_moi : sous quel angle IL est dans MON champ — l'agent regarde vers l'objectif
            vv = defs[k,:2] - p[i]
            gis_moi = math.degrees(math.atan2(vv[0], vv[1])) % 360
            cap = math.degrees(math.atan2(-p[i][0], -p[i][1])) % 360
            a_moi = abs(((gis_moi - cap + 180) % 360) - 180)
            Ee[i, j] = [min(d[i,k],400)/400, ec[i,k]/180, a_moi/180]; Mm[i, j] = 1.0
    with torch.no_grad():
        r = m(torch.zeros(len(p),1,device=dev),
              torch.tensor(Ee,device=dev), torch.tensor(Mm,device=dev)).cpu().numpy()
    EX.append(e); RI.append(r)

EX = np.concatenate(EX); RI = np.concatenate(RI)
rang = lambda v: np.argsort(np.argsort(v)).astype(float)
rho = float(np.corrcoef(rang(EX), rang(RI))[0,1])

print("\n" + "="*68)
print(f"  {len(EX)} etats traverses par l'agent, sur 20 configurations")
print(f"  correlation de rang entre expo et le risque appris : rho = {rho:+.3f}")
print(f"  (critere ecrit avant : |rho| < 0,5 pour que la substitution ait un sens)")
print("="*68)
if abs(rho) < 0.5:
    print("  ILS ORDONNENT DIFFEREMMENT. Substituer PEUT changer la politique apprise.")
    print("  -> on peut engager le re-entrainement.")
else:
    print("  ILS ORDONNENT PAREIL. Substituer ne changera rien a ce que l'agent apprend :")
    print("  inutile de payer le re-entrainement pour le decouvrir.")
