import sys, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")   # l'env PARTIEL patche
from assault_partial import AssaultTerrain
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
REPLICA = "/home/younes/arma3-marl/replica.npz"
KW = dict(A=1, D=2, relief=40.0, hit=0.16, max_steps=60, shell_obs=True, replica=True, replica_path=REPLICA, partial=True, world_shell=True)


class GRUPol(nn.Module):
    def __init__(self, O, A, H=256):
        super().__init__(); self.gru = nn.GRU(O, H, batch_first=True); self.pi = nn.Linear(H, A); self.v = nn.Linear(H, 1); self.H = H
    def step(self, x, h):
        out, h2 = self.gru(x.unsqueeze(1), h); o = out.squeeze(1); return self.pi(o), self.v(o).squeeze(-1), h2


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def train_mlp(seed, iters=300, envs=8192, rollout=16):
    torch.manual_seed(seed)
    env = AssaultTerrain(num_envs=envs, device=DEV, seed=seed, **KW)
    O, NA = env.obs_dim, env.n_actions; net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset(); rr = 0.0
    for it in range(iters):
        OB = torch.zeros(rollout, envs, 1, O, device=DEV); AC = torch.zeros(rollout, envs, 1, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, envs, 1, device=DEV); VL = torch.zeros(rollout, envs, device=DEV); RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        neut = nep = 0
        for t in range(rollout):
            with torch.no_grad():
                logits = net.a_logits(obs); dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act)
            if rw.dim() > 1: rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done; obs = nobs; dm = done.bool()
            if dm.any(): neut += info["neutralized"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6); advA = adv.unsqueeze(-1).expand(rollout, envs, 1)
        ob = OB.reshape(-1, 1, O); ac = AC.reshape(-1, 1); oldlp = LP.reshape(-1, 1); advf = advA.reshape(-1, 1); retf = ret.reshape(-1)
        for ep in range(4):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * advf, torch.clamp(ratio, 0.8, 1.2) * advf).mean(); vl = ((net.value(ob) - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = neut / max(nep, 1)
    return rr


def train_gru(seed, iters=300, envs=8192, rollout=16, H=256):
    torch.manual_seed(seed)
    env = AssaultTerrain(num_envs=envs, device=DEV, seed=seed, **KW)
    O, NA = env.obs_dim, env.n_actions; net = GRUPol(O, NA, H).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset()[:, 0, :]; h = torch.zeros(1, envs, H, device=DEV); rr = 0.0
    for it in range(iters):
        OB = torch.zeros(rollout, envs, O, device=DEV); H0 = h.detach().clone()
        AC = torch.zeros(rollout, envs, dtype=torch.long, device=DEV); LP = torch.zeros(rollout, envs, device=DEV); VL = torch.zeros(rollout, envs, device=DEV); RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        neut = nep = 0
        for t in range(rollout):
            with torch.no_grad():
                logits, val, h = net.step(obs, h); dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act)
            nobs, rw, done, info = env.step(act.unsqueeze(1))
            if rw.dim() > 1: rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done; obs = nobs[:, 0, :]; h = h * (1.0 - done).view(1, envs, 1); dm = done.bool()
            if dm.any(): neut += info["neutralized"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad(): _, lastv, _ = net.step(obs, h)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        for ep in range(4):
            h2 = H0; lg_l = []; v_l = []
            for t in range(rollout):
                lg, vv, h2 = net.step(OB[t], h2); lg_l.append(lg); v_l.append(vv); h2 = h2 * (1.0 - DN[t]).view(1, envs, 1)
            logits = torch.stack(lg_l); val = torch.stack(v_l); dist = torch.distributions.Categorical(logits=logits); lp = dist.log_prob(AC); ratio = (lp - LP).exp()
            pl = -torch.min(ratio * adv, torch.clamp(ratio, 0.8, 1.2) * adv).mean(); vl = ((val - ret) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = neut / max(nep, 1)
    return rr


print("=== OBS PARTIELLE (ennemi masque hors-vue) : MLP (reflexe) vs GRU (memoire) ===", flush=True)
mlp = [train_mlp(s) for s in range(2)]
print(">>> MLP : %s  moy %.0f%%" % ([round(100*x) for x in mlp], 100*sum(mlp)/len(mlp)), flush=True)
gru = [train_gru(s) for s in range(2)]
print(">>> GRU : %s  moy %.0f%%" % ([round(100*x) for x in gru], 100*sum(gru)/len(gru)), flush=True)
print("PARTIAL FINI", flush=True)
