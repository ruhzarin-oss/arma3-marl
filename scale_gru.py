import sys, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"
REPLICA = "/home/younes/arma3-marl/replica.npz"


class GRUPol(nn.Module):
    def __init__(self, O, A, H=256):
        super().__init__()
        self.gru = nn.GRU(O, H, batch_first=True)
        self.pi = nn.Linear(H, A); self.v = nn.Linear(H, 1); self.H = H

    def step(self, x, h):                 # x:[N,O]  h:[1,N,H]
        out, h2 = self.gru(x.unsqueeze(1), h)   # out:[N,1,H]
        o = out.squeeze(1)
        return self.pi(o), self.v(o).squeeze(-1), h2


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def train(seed=0, iters=200, envs=8192, rollout=16, H=256):
    torch.manual_seed(seed)
    env = AssaultTerrain(num_envs=envs, A=1, D=2, relief=40.0, hit=0.16, max_steps=60, device=DEV, seed=seed,
                         shell_obs=True, replica=True, replica_path=REPLICA)
    O, NA = env.obs_dim, env.n_actions
    net = GRUPol(O, NA, H).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset()[:, 0, :]; h = torch.zeros(1, envs, H, device=DEV); rr = 0.0
    for it in range(iters):
        OB = torch.zeros(rollout, envs, O, device=DEV); H0 = h.detach().clone()
        AC = torch.zeros(rollout, envs, dtype=torch.long, device=DEV); LP = torch.zeros(rollout, envs, device=DEV)
        VL = torch.zeros(rollout, envs, device=DEV); RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        neut = nep = 0
        for t in range(rollout):
            with torch.no_grad():
                logits, val, h = net.step(obs, h)
                dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act)
            nobs, rw, done, info = env.step(act.unsqueeze(1))
            if rw.dim() > 1: rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done
            obs = nobs[:, 0, :]; dm = done.bool()
            h = h * (1.0 - done).view(1, envs, 1)            # reset memoire en fin d'episode
            if dm.any(): neut += info["neutralized"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad():
            _, lastv, _ = net.step(obs, h)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        for ep in range(4):
            h2 = H0; logits_l = []; val_l = []
            for t in range(rollout):
                lg, vv, h2 = net.step(OB[t], h2)
                logits_l.append(lg); val_l.append(vv)
                h2 = h2 * (1.0 - DN[t]).view(1, envs, 1)
            logits = torch.stack(logits_l); val = torch.stack(val_l)
            dist = torch.distributions.Categorical(logits=logits)
            lp = dist.log_prob(AC); ratio = (lp - LP).exp()
            s1 = ratio * adv; s2 = torch.clamp(ratio, 0.8, 1.2) * adv; pl = -torch.min(s1, s2).mean()
            vl = ((val - ret) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = neut / max(nep, 1)
        if it % 40 == 0: print("  it %3d | neutralises %.0f%%" % (it, 100 * rr), flush=True)
    return rr


import sys as _s
N = int(_s.argv[1]) if len(_s.argv) > 1 else 3
IT = int(_s.argv[2]) if len(_s.argv) > 2 else 200
print("=== GRU (memoire) sur replica cover-only : %d graines x %d it ===" % (N, IT), flush=True)
sc = [train(seed=s, iters=IT) for s in range(N)]
print(">>> GRU scores=%s | succes %d/%d" % ([round(100 * x) for x in sc], sum(1 for x in sc if x > 0.4), N), flush=True)
print("GRU FINI", flush=True)
