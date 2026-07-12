"""sharingan_clone — CLONAGE. Entraine notre Net (dim_obs->4) en supervise a predire l'action experte depuis
l'obs (corpus sharingan_demos14.npz, obs INCARNEE a 14 features). Split train/val, poids de classe. On compare
l'accuracy au baseline 'classe majoritaire' : si ca decolle, la perception enrichie etait bien le mur."""
import sys
import numpy as np
import torch
import torch.nn as nn
from train_koth_gpu import Net
DEV = "cuda:0"
PATH = sys.argv[1] if len(sys.argv) > 1 else "/home/younes/arma3-marl/staff/sharingan_demos14.npz"
d = np.load(PATH); X, y = d["X"], d["y"]
n, dim = X.shape
rng = np.random.default_rng(0); idx = np.arange(n); rng.shuffle(idx)
sp = int(n * 0.8); tr, va = idx[:sp], idx[sp:]
Xtr = torch.tensor(X[tr], device=DEV); ytr = torch.tensor(y[tr], dtype=torch.long, device=DEV)
Xva = torch.tensor(X[va], device=DEV); yva = torch.tensor(y[va], dtype=torch.long, device=DEV)
net = Net(dim, 4, 512, 3).to(DEV)                                  # entrainement FRAIS (dim obs a change)
cnt = np.bincount(y, minlength=4)
w = torch.tensor(cnt.sum() / (4 * np.maximum(cnt, 1)), dtype=torch.float32, device=DEV)
lossf = nn.CrossEntropyLoss(weight=w)
opt = torch.optim.Adam(net.parameters(), lr=2e-3)
print("corpus : %d | obs dim %d | train %d / val %d | classes %s" % (n, dim, len(tr), len(va), dict(zip(range(4), cnt.tolist()))), flush=True)
for ep in range(601):
    opt.zero_grad(); loss = lossf(net.a_logits(Xtr), ytr); loss.backward(); opt.step()
    if ep % 120 == 0:
        with torch.no_grad():
            tra = (net.a_logits(Xtr).argmax(1) == ytr).float().mean().item()
            vaa = (net.a_logits(Xva).argmax(1) == yva).float().mean().item()
        print("ep %3d | loss %.3f | acc train %.2f | acc val %.2f" % (ep, loss.item(), tra, vaa), flush=True)
with torch.no_grad():
    pv = net.a_logits(Xva).argmax(1).cpu().numpy()
yv = y[va]
torch.save(net.state_dict(), "/home/younes/arma3-marl/koth_lambs_cloned14.pt")
base = cnt.max() / cnt.sum()
print("\n>>> CLONE INCARNE val acc = %.3f  (baseline classe-majoritaire = %.3f) | obs10 etait 0.44" % ((pv == yv).mean(), base), flush=True)
for c, nm in enumerate(["tenir", "avancer", "suppresser", "couvert"]):
    msk = yv == c
    if msk.sum():
        print("   %-11s : rappel %.2f (n=%d)" % (nm, (pv[msk] == c).mean(), int(msk.sum())), flush=True)
print("CLONE FINI")
