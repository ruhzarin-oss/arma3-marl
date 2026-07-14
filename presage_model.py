#!/usr/bin/env python3
"""presage_model.py — GRU d'anticipation : K frames -> exposition dans L pas. MSE, auto-supervise.
GATE : battre la PERSISTANCE (predire = exposition actuelle). smoke: python presage_model.py smoke"""
import numpy as np, torch, torch.nn as nn, sys
torch.backends.cudnn.enabled = False              # GRU sans cuDNN -> marche meme sur GPU SM<7.5 (GTX 1060)
DEV = "cuda:0"
SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
d = np.load("/home/younes/arma3-marl/presage_data.npz")
X = torch.tensor(d["X"]).float(); Ynow = torch.tensor(d["Ynow"]).float(); Yf = torch.tensor(d["Yfut"]).float()
O = int(d["O"])
n = X.shape[0]; g = torch.Generator().manual_seed(0); idx = torch.randperm(n, generator=g)
X, Ynow, Yf = X[idx], Ynow[idx], Yf[idx]
ntr = int(0.8 * n)
Xtr, Yftr = X[:ntr].to(DEV), Yf[:ntr].to(DEV)
Xte, Yfte, Ynte = X[ntr:].to(DEV), Yf[ntr:].to(DEV), Ynow[ntr:].to(DEV)


class GRUp(nn.Module):
    def __init__(s, O, h=128):
        super().__init__(); s.g = nn.GRU(O, h, batch_first=True); s.f = nn.Linear(h, 1)

    def forward(s, x):
        _, hn = s.g(x); return s.f(hn[-1]).squeeze(-1)


net = GRUp(O).to(DEV); opt = torch.optim.Adam(net.parameters(), 1e-3); lf = nn.MSELoss()
EPO = 2 if SMOKE else 30; B = 8192
for ep in range(EPO):
    net.train(); p = torch.randperm(Xtr.shape[0], device=DEV)
    for i in range(0, Xtr.shape[0], B):
        j = p[i:i + B]; opt.zero_grad(); lf(net(Xtr[j]), Yftr[j]).backward(); opt.step()
    if ep % 5 == 0 or SMOKE:
        net.eval()
        with torch.no_grad(): print("ep %2d  test MSE %.4f" % (ep, lf(net(Xte), Yfte).item()), flush=True)

net.eval()
with torch.no_grad():
    mse_net = lf(net(Xte), Yfte).item()
    mse_pers = lf(Ynte, Yfte).item()                 # PERSISTANCE : predire l'expo dans L = l'expo maintenant
    mse_mean = lf(torch.full_like(Yfte, Yftr.mean()), Yfte).item()
print("\n=== GATE anticipation ===", flush=True)
print("  GRU         MSE %.4f" % mse_net)
print("  persistance MSE %.4f  (predire = maintenant)" % mse_pers)
print("  moyenne     MSE %.4f" % mse_mean)
print("  -> GRU bat la persistance (global) : %s" % ("OUI" if mse_net < mse_pers * 0.95 else "non"))
# LE VRAI test : sur les TRANSITIONS (exposition qui flippe entre maintenant et +L)
tr = (Yfte - Ynte).abs() > 0.5
with torch.no_grad(): pred = net(Xte)
if int(tr.sum()) > 0:
    mnt = lf(pred[tr], Yfte[tr]).item(); mpt = lf(Ynte[tr], Yfte[tr]).item()
    print("\n=== TRANSITIONS (%d, %.1f%% des cas) — LA valeur d'anticipation ===" % (int(tr.sum()), 100 * tr.float().mean()))
    print("  GRU         MSE %.4f" % mnt)
    print("  persistance MSE %.4f" % mpt)
    print("  -> GRU anticipe les flips mieux que la persistance : %s" % ("OUI" if mnt < mpt * 0.9 else "non"), flush=True)
if not SMOKE:
    torch.save(net.state_dict(), "/home/younes/arma3-marl/presage.pt"); print("sauve presage.pt")
