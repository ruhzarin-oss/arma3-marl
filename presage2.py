#!/usr/bin/env python3
"""presage2.py — E2 : anticipation ENRICHIE. En plus de l'exposition future, predit la DIRECTION de la
menace future (sin/cos du cap vers le defenseur qui aura le LOS) -> anticipation OFFENSIVE (s'orienter/se
placer sur un angle sur), pas juste survie. GRU 3 sorties, auto-supervise. smoke: python presage2.py smoke"""
import sys, math, torch, torch.nn as nn, numpy as np
torch.backends.cudnn.enabled = False
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"; MAP = "/home/younes/arma3-marl/replica_athens.npz"
K, L, N, EP, T = 4, 3, 512, 3, 60
SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
if SMOKE: EP = 1; N = 128


def mkenv(sd):
    return AssaultTerrain(num_envs=N, A=9, D=6, R_spawn=130, relief=40.0, hit=0.0, shell_obs=True,
                          team_obs=True, replica=True, replica_path=MAP, max_steps=T, device=DEV, seed=sd)


@torch.no_grad()
def threat_bearing(e):
    """cap (sin,cos) vers le defenseur vivant en LOS+portee le plus proche ; (0,0) si aucun."""
    N_, A = e.apx.shape; best_d = torch.full((N_, A), 1e18, device=DEV); bsin = torch.zeros(N_, A, device=DEV); bcos = torch.zeros(N_, A, device=DEV)
    for di in range(e.D):
        bx = e.dpx[:, di:di + 1].expand(N_, A); by = e.dpy[:, di:di + 1].expand(N_, A)
        los = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale, eye_a=e._eye(), eye_b=1.7)
        dist = torch.sqrt((e.apx - bx) ** 2 + (e.apy - by) ** 2)
        ok = (los > 0.5) & (dist < e.fire_range) & e._dalive()[:, di:di + 1] & (dist < best_d)
        th = torch.atan2(bx - e.apx, by - e.apy)
        best_d = torch.where(ok, dist, best_d); bsin = torch.where(ok, torch.sin(th), bsin); bcos = torch.where(ok, torch.cos(th), bcos)
    return bsin, bcos


import math as _m
Xs, Ye, Ysin, Ycos = [], [], [], []
for ep in range(EP):
    e = mkenv(ep); o = e.reset(); obs, exp, bs, bc = [], [], [], []
    for t in range(T):
        th = torch.atan2(-e.apx, -e.apy); a = (torch.round(th / (_m.pi / 4)) % 8).long()
        rnd = torch.randint(0, 8, a.shape, device=DEV); m = torch.rand(a.shape, device=DEV) < 0.5; a = torch.where(m, rnd, a)
        o, _, _, info = e.step(a, auto_reset=False)
        s, c = threat_bearing(e); obs.append(o.detach()); exp.append(e.last_exposed.detach()); bs.append(s); bc.append(c)
    obs = torch.stack(obs); exp = torch.stack(exp); bs = torch.stack(bs); bc = torch.stack(bc)
    Tt, Nn, Aa, O = obs.shape
    obs = obs.permute(1, 2, 0, 3).reshape(Nn * Aa, Tt, O)
    for arr, dst in ((exp, Ye), (bs, Ysin), (bc, Ycos)): arr2 = arr.permute(1, 2, 0).reshape(Nn * Aa, Tt)
    exp = exp.permute(1, 2, 0).reshape(Nn * Aa, Tt); bs = bs.permute(1, 2, 0).reshape(Nn * Aa, Tt); bc = bc.permute(1, 2, 0).reshape(Nn * Aa, Tt)
    for t in range(K - 1, Tt - L):
        Xs.append(obs[:, t - K + 1:t + 1, :].half().cpu()); Ye.append(exp[:, t + L].cpu()); Ysin.append(bs[:, t + L].cpu()); Ycos.append(bc[:, t + L].cpu())
X = torch.cat(Xs).float(); Ye = torch.cat(Ye); Ysin = torch.cat(Ysin); Ycos = torch.cat(Ycos); O = X.shape[-1]
print("dataset X", tuple(X.shape), "| menace non-nulle %.1f%%" % (100 * (Ysin.abs() + Ycos.abs() > 0).float().mean()), flush=True)

n = X.shape[0]; idx = torch.randperm(n, generator=torch.Generator().manual_seed(0)); X, Ye, Ysin, Ycos = X[idx], Ye[idx], Ysin[idx], Ycos[idx]
ntr = int(0.8 * n)
Xtr = X[:ntr].to(DEV); Ytr = torch.stack([Ye, Ysin, Ycos], 1)[:ntr].to(DEV)
Xte = X[ntr:].to(DEV); Yte = torch.stack([Ye, Ysin, Ycos], 1)[ntr:].to(DEV)


class GRU3(nn.Module):
    def __init__(s, O, h=128):
        super().__init__(); s.g = nn.GRU(O, h, batch_first=True); s.f = nn.Linear(h, 3)
    def forward(s, x):
        _, hn = s.g(x); return s.f(hn[-1])


net = GRU3(O).to(DEV); opt = torch.optim.Adam(net.parameters(), 1e-3)
for ep in range(2 if SMOKE else 30):
    p = torch.randperm(Xtr.shape[0], device=DEV)
    for i in range(0, Xtr.shape[0], 8192):
        j = p[i:i + 8192]; opt.zero_grad(); ((net(Xtr[j]) - Ytr[j]) ** 2).mean().backward(); opt.step()
net.eval()
with torch.no_grad():
    pred = net(Xte); tr = (Yte[:, 1].abs() + Yte[:, 2].abs() > 0.1)                # cas avec vraie menace
    exp_mse = ((pred[:, 0] - Yte[:, 0]) ** 2).mean().item()
    # direction : cosine similarity entre (sin,cos) predit et vrai, sur les cas de menace
    pv = pred[tr, 1:]; tv = Yte[tr, 1:]; cos = (pv * tv).sum(1) / (pv.norm(dim=1).clamp(min=1e-3) * tv.norm(dim=1).clamp(min=1e-3))
print("\n=== E2 : anticipation enrichie (exposition + DIRECTION menace) ===")
print("  exposition future  : MSE %.4f" % exp_mse)
print("  direction menace   : cos-sim %.3f sur %d cas de menace  (1=parfait, 0=aleatoire)" % (cos.mean().item(), int(tr.sum())))
print("  -> le modele anticipe D'OU vient le feu : %s" % ("OUI" if cos.mean().item() > 0.3 else "faible"))
