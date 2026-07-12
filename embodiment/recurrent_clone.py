"""recurrent_clone (etape 1 / memoire) — entraine un cerveau A MEMOIRE (GRU) sur les SEQUENCES LAMBS, et le compare
au MLP SANS memoire sur EXACTEMENT les memes donnees. Mesure ce que la memoire apporte (surtout sur 'avancer',
l'action qui depend du contexte/historique). Sauve le cerveau recurrent -> koth_lambs_gru14.pt."""
import sys
import numpy as np
import torch
import torch.nn as nn
torch.backends.cudnn.enabled = False           # GRU sans cuDNN (compat GPU secondaire, corpus minuscule)
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
PATH = sys.argv[1] if len(sys.argv) > 1 else "/home/younes/arma3-marl/staff/sharingan_seq14.npz"
ACTS = ["tenir", "avancer", "suppresser", "couvert"]


class RecurrentBrain(nn.Module):
    """Cerveau a MEMOIRE : un GRU entretient un etat mental qui se met a jour a chaque pas -> il se souvient."""
    def __init__(self, obs_dim=14, n_act=4, hidden=128):
        super().__init__()
        self.gru = nn.GRU(obs_dim, hidden, batch_first=True)
        self.head = nn.Linear(hidden, n_act)

    def forward(self, x, h=None):           # x:[B,T,D] -> logits:[B,T,A]
        out, h = self.gru(x, h); return self.head(out), h

    def step(self, x1, h=None):             # x1:[B,D] un seul pas (deploiement temps reel) -> logits:[B,A], h
        out, h = self.gru(x1.unsqueeze(1), h); return self.head(out.squeeze(1)), h


d = np.load(PATH)
X = torch.tensor(d["X"], device=DEV); Y = torch.tensor(d["y"], dtype=torch.long, device=DEV); L = d["lengths"]
N, T, D = X.shape
rng = np.random.default_rng(0); idx = np.arange(N); rng.shuffle(idx)
sp = int(N * 0.8); tr, va = idx[:sp], idx[sp:]
mask = (Y >= 0).float()                                    # [N,T] 1 sur les pas valides
# poids de classe (sur les pas valides)
flatY = Y[Y >= 0].cpu().numpy(); cnt = np.bincount(flatY, minlength=4)
w = torch.tensor(cnt.sum() / (4 * np.maximum(cnt, 1)), dtype=torch.float32, device=DEV)
print("corpus : %d sequences | T_max %d | pas valides %d | classes %s" % (N, T, int(mask.sum().item()), dict(zip(ACTS, cnt.tolist()))), flush=True)


def masked_acc(logits, y, m):
    pred = logits.argmax(-1)
    ok = ((pred == y).float() * m).sum().item(); tot = m.sum().item()
    return ok / max(tot, 1), pred


def per_class_recall(pred, y, m):
    out = {}
    for c in range(4):
        sel = (y == c) & (m > 0)
        if sel.any():
            out[ACTS[c]] = ((pred == c) & sel).float().sum().item() / sel.float().sum().item()
    return out


# ---------- 1) CERVEAU A MEMOIRE (GRU) ----------
net = RecurrentBrain(D, 4, 128).to(DEV)
lossf = nn.CrossEntropyLoss(weight=w, reduction="none")
opt = torch.optim.Adam(net.parameters(), lr=2e-3)
Xtr, Ytr, Mtr = X[tr], Y[tr].clamp(min=0), mask[tr]
Xva, Yva, Mva = X[va], Y[va].clamp(min=0), mask[va]
for ep in range(401):
    opt.zero_grad()
    logits, _ = net(Xtr)
    loss = (lossf(logits.reshape(-1, 4), Ytr.reshape(-1)).reshape(Ytr.shape) * Mtr).sum() / Mtr.sum()
    loss.backward(); opt.step()
    if ep % 100 == 0:
        with torch.no_grad():
            lv, _ = net(Xva); va_acc, _ = masked_acc(lv, Yva, Mva)
        print("GRU ep %3d | loss %.3f | val acc %.3f" % (ep, loss.item(), va_acc), flush=True)
with torch.no_grad():
    lv, _ = net(Xva); gru_acc, gru_pred = masked_acc(lv, Yva, Mva)
    gru_rec = per_class_recall(gru_pred, Yva, Mva)

# ---------- 2) MLP SANS memoire (memes pas, mais melanges, aucun contexte temporel) ----------
mlp = Net(D, 4, 512, 3).to(DEV)
Xf_tr = Xtr[Mtr > 0]; Yf_tr = Ytr[Mtr > 0]; Xf_va = Xva[Mva > 0]; Yf_va = Yva[Mva > 0]
lf = nn.CrossEntropyLoss(weight=w); om = torch.optim.Adam(mlp.parameters(), lr=2e-3)
for ep in range(601):
    om.zero_grad(); l = lf(mlp.a_logits(Xf_tr), Yf_tr); l.backward(); om.step()
with torch.no_grad():
    mp = mlp.a_logits(Xf_va).argmax(1)
    mlp_acc = (mp == Yf_va).float().mean().item()
    mlp_rec = {ACTS[c]: (((mp == c) & (Yf_va == c)).float().sum() / max((Yf_va == c).float().sum().item(), 1)).item() for c in range(4) if (Yf_va == c).any()}

torch.save(net.state_dict(), "/home/younes/arma3-marl/koth_lambs_gru14.pt")
base = cnt.max() / cnt.sum()
print("\n==================== MEMOIRE vs SANS MEMOIRE ====================", flush=True)
print(">>> MLP (sans memoire) : val acc %.3f" % mlp_acc, flush=True)
print(">>> GRU (avec memoire) : val acc %.3f   (baseline classe-majoritaire %.3f)" % (gru_acc, base), flush=True)
print("rappel par action :", flush=True)
for c in ACTS:
    print("   %-11s : MLP %.2f | GRU %.2f" % (c, mlp_rec.get(c, 0), gru_rec.get(c, 0)), flush=True)
print("cerveau a memoire sauve -> koth_lambs_gru14.pt", flush=True)
print("RECUR FINI", flush=True)
