"""COMMANDANT APPRIS (incrément 2) — PPO CONTINU sur CommanderEnv : la politique place les K elements
(positions cibles continues), le bas-niveau execute, AssaultTerrain simule. Curriculum D=4->6->8.
Mesure : % colis securise / % defense neutralisee / % survie. But : depasser le commandant code-main (~13%)."""
import sys, math, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)

    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def mkenv(N, D, seed): return CommanderEnv(N, A=8, K=4, D=D, device=DEV, seed=seed, max_steps=120)  # DURCI : 4 elements, +de temps


def evalrun(net, D, envs=2048, steps=16, seed=999):
    e = mkenv(envs, D, seed); obs = e.reset(); sec = neu = surv = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs); a = mu.view(envs, e.K, 2)            # greedy
            obs, rew, done, info = e.step(a)
            if done.any():
                dm = done
                sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / 8)[dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1)


probe = mkenv(2, 8, 0); O = probe.obs_dim; AC = probe.act_dim; K = probe.K
net = CNet(O, AC, 256).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== COMMANDANT DURCI : PPO continu, K=4 elements, curriculum D=4->8->12 (obs=%d act=%d) ===" % (O, AC), flush=True)
N = 4096; rollout = 12
for D in [4, 8, 12]:
    env = mkenv(N, D, 0); obs = env.reset()
    for it in range(180):
        OB = torch.zeros(rollout, N, O, device=DEV); ACT = torch.zeros(rollout, N, AC, device=DEV)
        LP = torch.zeros(rollout, N, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                mu, v = net(obs); std = net.log_std.exp(); dist = torch.distributions.Normal(mu, std)
                a = dist.sample(); lp = dist.log_prob(a).sum(-1)
            nobs, rw, done, info = env.step(a.view(N, K, 2))
            OB[t] = obs; ACT[t] = a; LP[t] = lp; VL[t] = v; RW[t] = rw; DN[t] = done.float()
            env.reset_done(done); obs = env._obs()
        with torch.no_grad(): _, lastv = net(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        ob = OB.reshape(-1, O); ac = ACT.reshape(-1, AC); oldlp = LP.reshape(-1); af = adv.reshape(-1); rf = ret.reshape(-1)
        for ep in range(4):
            mu, v = net(ob); std = net.log_std.exp(); dist = torch.distributions.Normal(mu, std)
            lp = dist.log_prob(ac).sum(-1); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * af, torch.clamp(ratio, 0.8, 1.2) * af).mean()
            vl = ((v - rf) ** 2).mean(); ent = dist.entropy().sum(-1).mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 30 == 0:
            s, n, sv = evalrun(net, D); print("   D=%d it %3d | securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % (D, it, s, n, sv), flush=True)
    s, n, sv = evalrun(net, D); print(">>> PALIER D=%d : securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % (D, s, n, sv), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/commander_k4_d%d.pt" % D)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/commander_k4.pt")
print("COMMANDANT DURCI FINI -> commander_k4.pt", flush=True)
