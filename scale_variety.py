import sys, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"
REPLICA = "/home/younes/arma3-marl/replica.npz"


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


def evalrate(net, env, hitval, H, steps=120):
    env.hit = float(hitval); env._reset(torch.arange(env.N, device=DEV)); obs = env._obs()[:, 0, :]
    h = torch.zeros(1, env.N, H, device=DEV); neut = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            logits, _, h = net.step(obs, h); act = logits.argmax(-1)
            nobs, rw, done, info = env.step(act.unsqueeze(1)); obs = nobs[:, 0, :]
            h = h * (1.0 - done).view(1, env.N, 1); dm = done.bool()
            if dm.any(): neut += info["neutralized"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * neut / max(nep, 1)


def train(seed=0, iters=250, envs=8192, rollout=16, H=256):
    torch.manual_seed(seed)
    env = AssaultTerrain(num_envs=envs, A=1, D=2, relief=40.0, hit=0.16, max_steps=60, device=DEV, seed=seed,
                         shell_obs=True, replica=True, replica_path=REPLICA)
    env.hit = (torch.rand(envs, 1, device=DEV) * 0.10 + 0.08)     # VARIETE : chaque env un hit dans [0.08, 0.18]
    O, NA = env.obs_dim, env.n_actions
    net = GRUPol(O, NA, H).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset()[:, 0, :]; h = torch.zeros(1, envs, H, device=DEV)
    for it in range(iters):
        OB = torch.zeros(rollout, envs, O, device=DEV); H0 = h.detach().clone()
        AC = torch.zeros(rollout, envs, dtype=torch.long, device=DEV); LP = torch.zeros(rollout, envs, device=DEV)
        VL = torch.zeros(rollout, envs, device=DEV); RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                logits, val, h = net.step(obs, h); dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act)
            nobs, rw, done, info = env.step(act.unsqueeze(1))
            if rw.dim() > 1: rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done
            obs = nobs[:, 0, :]; h = h * (1.0 - done).view(1, envs, 1)
        with torch.no_grad(): _, lastv, _ = net.step(obs, h)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        for ep in range(4):
            h2 = H0; lg_l = []; v_l = []
            for t in range(rollout):
                lg, vv, h2 = net.step(OB[t], h2); lg_l.append(lg); v_l.append(vv); h2 = h2 * (1.0 - DN[t]).view(1, envs, 1)
            logits = torch.stack(lg_l); val = torch.stack(v_l); dist = torch.distributions.Categorical(logits=logits)
            lp = dist.log_prob(AC); ratio = (lp - LP).exp(); s1 = ratio * adv; s2 = torch.clamp(ratio, 0.8, 1.2) * adv
            pl = -torch.min(s1, s2).mean(); vl = ((val - ret) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
    return net, env


print("=== ETAPE 2 VARIETE : GRU entraine sur hit aleatoire [0.08,0.18], evalue par letalite ===", flush=True)
net, env = train()
for hv in [0.10, 0.14, 0.18]:
    print(">>> eval hit=%.2f : neutralises %.0f%%" % (hv, evalrate(net, env, hv, 256)), flush=True)
print("VARIETE FINI", flush=True)
