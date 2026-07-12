"""COMMANDANT MAAC (option 4) — critique a ATTENTION pour debloquer la coordination a K=4 elements.
- ACTEUR partage par element : obs LOCALE (7 features de l'element + 3 globales) -> sa position cible (2D).
- CRITIQUE CENTRALISE a ATTENTION : pour la valeur de chaque element, il ATTEND sur les autres elements
  (apprend qui compte pour qui) au lieu de tout concatener -> meilleur credit assignment -> coordination.
PPO multi-agent (1 agent = 1 element), recompense d'equipe partagee. Curriculum D=4->8->12.
Compare au concatene qui CASSE a K=4 (D=8 35%, D=12 10%)."""
import sys, math, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"; K = 4


class Actor(nn.Module):                                        # politique PARTAGEE par element (obs locale -> position)
    def __init__(self, obs=10, h=128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 2))
        self.log_std = nn.Parameter(torch.zeros(2) - 0.5)

    def forward(self, o): return self.net(o)


class AttnCritic(nn.Module):                                   # critique CENTRALISE a ATTENTION (chaque element attend les autres)
    def __init__(self, obs=10, d=64):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(obs, d), nn.Tanh())
        self.q = nn.Linear(d, d); self.k = nn.Linear(d, d); self.v = nn.Linear(d, d)
        self.val = nn.Sequential(nn.Linear(2 * d, d), nn.Tanh(), nn.Linear(d, 1)); self.d = d

    def forward(self, obs):                                    # obs (N,K,10) -> V (N,K)
        h = self.enc(obs)
        att = torch.softmax(self.q(h) @ self.k(h).transpose(1, 2) / math.sqrt(self.d), dim=-1)  # (N,K,K)
        ctx = att @ self.v(h)                                  # (N,K,d) : ce que chaque element retient des autres
        return self.val(torch.cat([h, ctx], -1)).squeeze(-1)


def per_elem(obs):                                             # (N,7K+3) -> (N,K,10) : 7 locales de l'element + 3 globales
    g = obs[:, 7 * K:]; els = obs[:, :7 * K].reshape(obs.shape[0], K, 7)
    return torch.cat([els, g.unsqueeze(1).expand(-1, K, -1)], -1)


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):           # (T,N,K)
    T, N, Kk = rew.shape; adv = torch.zeros(T, N, Kk, device=rew.device); g = torch.zeros(N, Kk, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def mkenv(N, D, seed): return CommanderEnv(N, A=8, K=K, D=D, device=DEV, seed=seed, max_steps=120)


actor = Actor().to(DEV); critic = AttnCritic().to(DEV)
opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4)


def evalrun(D, envs=2048, steps=18, seed=999):
    e = mkenv(envs, D, seed); obs = e.reset(); sec = neu = surv = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu = actor(per_elem(obs))
            obs, rew, done, info = e.step(mu)
            if done.any():
                dm = done; sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / 8)[dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1)


print("=== COMMANDANT MAAC : acteur partage + critique ATTENTION, K=4, D=4->8->12 ===", flush=True)
N = 4096; rollout = 12
for D in [4, 8, 12]:
    env = mkenv(N, D, 0); obs = env.reset()
    for it in range(180):
        OB = torch.zeros(rollout, N, K, 10, device=DEV); ACT = torch.zeros(rollout, N, K, 2, device=DEV)
        LP = torch.zeros(rollout, N, K, device=DEV); VL = torch.zeros(rollout, N, K, device=DEV)
        RW = torch.zeros(rollout, N, K, device=DEV); DN = torch.zeros(rollout, N, K, device=DEV)
        for t in range(rollout):
            po = per_elem(obs)
            with torch.no_grad():
                mu = actor(po); std = actor.log_std.exp(); dist = torch.distributions.Normal(mu, std)
                a = dist.sample(); lp = dist.log_prob(a).sum(-1); val = critic(po)
            nobs, rw, done, info = env.step(a)
            OB[t] = po; ACT[t] = a; LP[t] = lp; VL[t] = val
            RW[t] = rw.unsqueeze(1).expand(-1, K); DN[t] = done.float().unsqueeze(1).expand(-1, K)
            env.reset_done(done); obs = env._obs()
        with torch.no_grad(): lastv = critic(per_elem(obs))
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        ob = OB.reshape(-1, K, 10); ac = ACT.reshape(-1, K, 2); oldlp = LP.reshape(-1, K); af = adv.reshape(-1, K); rf = ret.reshape(-1, K)
        for ep in range(4):
            mu = actor(ob); std = actor.log_std.exp(); dist = torch.distributions.Normal(mu, std)
            lp = dist.log_prob(ac).sum(-1); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * af, torch.clamp(ratio, 0.8, 1.2) * af).mean()
            vl = ((critic(ob) - rf) ** 2).mean(); ent = dist.entropy().sum(-1).mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(list(actor.parameters()) + list(critic.parameters()), 0.5); opt.step()
        if it % 30 == 0:
            s, n, sv = evalrun(D); print("   D=%d it %3d | securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % (D, it, s, n, sv), flush=True)
    s, n, sv = evalrun(D); print(">>> PALIER D=%d : securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % (D, s, n, sv), flush=True)
    torch.save({"actor": actor.state_dict(), "critic": critic.state_dict()}, "/home/younes/compose-embodiment/commander_maac_d%d.pt" % D)
torch.save({"actor": actor.state_dict(), "critic": critic.state_dict()}, "/home/younes/compose-embodiment/commander_maac.pt")
print("COMMANDANT MAAC FINI -> commander_maac.pt", flush=True)
