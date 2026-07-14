#!/usr/bin/env python3
"""presage_data.py — dataset d'ANTICIPATION (auto-supervise). Ennemis statiques -> cible = ma propre
EXPOSITION dans L pas. Sequences de K frames d'obs -> exposition future. Sauve presage_data.npz."""
import numpy as np, torch, math, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"; MAP = "/home/younes/arma3-marl/replica_athens.npz"
K, L, N, EP, T = 4, 3, 512, 3, 60


def mkenv(sd):
    return AssaultTerrain(num_envs=N, A=9, D=6, R_spawn=130, relief=40.0, hit=0.0, shell_obs=True,
                          team_obs=True, replica=True, replica_path=MAP, max_steps=T, device=DEV, seed=sd)


Xs, Yn, Yf = [], [], []
for ep in range(EP):
    e = mkenv(ep); o = e.reset(); obs, exp = [], []
    for t in range(T):
        th = torch.atan2(-e.apx, -e.apy); a = (torch.round(th / (math.pi / 4)) % 8).long()
        rnd = torch.randint(0, 8, a.shape, device=DEV); m = torch.rand(a.shape, device=DEV) < 0.5
        a = torch.where(m, rnd, a)                                  # 25% cap aleatoire -> trajectoires variees
        o, _, _, info = e.step(a, auto_reset=False)
        obs.append(o.detach()); exp.append(e.last_exposed.detach())
    obs = torch.stack(obs); exp = torch.stack(exp)                  # (T,N,A,O), (T,N,A)
    Tt, Nn, Aa, O = obs.shape
    obs = obs.permute(1, 2, 0, 3).reshape(Nn * Aa, Tt, O)          # (NA,T,O)
    exp = exp.permute(1, 2, 0).reshape(Nn * Aa, Tt)                # (NA,T)
    for t in range(K - 1, Tt - L):
        Xs.append(obs[:, t - K + 1:t + 1, :].half().cpu())        # (NA,K,O)
        Yn.append(exp[:, t].cpu())                                # exposition MAINTENANT (baseline persistance)
        Yf.append(exp[:, t + L].cpu())                            # exposition dans L pas (cible)
X = torch.cat(Xs); Yn = torch.cat(Yn); Yf = torch.cat(Yf)
np.savez("/home/younes/arma3-marl/presage_data.npz", X=X.numpy(), Ynow=Yn.numpy(), Yfut=Yf.numpy(),
         K=K, L=L, O=X.shape[-1])
print("dataset: X", tuple(X.shape), "-> Yfut", tuple(Yf.shape), "| obs_dim", X.shape[-1],
      "| expo moy now=%.3f fut=%.3f" % (Yn.mean(), Yf.mean()))
