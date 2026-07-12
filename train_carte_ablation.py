"""ABLATION CARTE — le commandant lit la VERITE-TERRAIN (OFF) vs la CARTE brouillard-memoire (ON).
Memes hyperparametres, meme seed, meme reseau. Mesure le "fog tax" : combien coute de ne plus voir
l'ennemi en clair. La version ON est la SEULE deployable en Arma (ou la verite n'existe pas) -> loi du +97.
Usage : python train_carte_ablation.py [iters=120] [N=2048] [D=8]
"""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"
ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 120
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
D = int(sys.argv[3]) if len(sys.argv) > 3 else 8
A, K, ROLL, MAXT = 8, 4, 12, 120


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)

    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, Nn = rew.shape; adv = torch.zeros(T, Nn, device=rew.device); g = torch.zeros(Nn, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def mkenv(n, seed, use_carte):
    return CommanderEnv(n, A=A, K=K, D=D, device=DEV, seed=seed, max_steps=MAXT, use_carte=use_carte)


def evalrun(net, use_carte, envs=2048, steps=16, seed=999):
    e = mkenv(envs, seed, use_carte); obs = e.reset(); sec = neu = surv = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs); a = mu.view(envs, K, 2)
            obs, rew, done, info = e.step(a)
            if done.any():
                dm = done
                sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / A)[dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1)


def train(use_carte, label):
    torch.manual_seed(0)
    probe = mkenv(2, 0, use_carte); O = probe.obs_dim; AC = probe.act_dim
    net = CNet(O, AC, 256).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    print("--- %s : PPO continu (obs=%d act=%d, N=%d, D=%d, %d iters) ---" % (label, O, AC, N, D, ITERS), flush=True)
    env = mkenv(N, 0, use_carte); obs = env.reset()
    for it in range(ITERS):
        OB = torch.zeros(ROLL, N, O, device=DEV); ACT = torch.zeros(ROLL, N, AC, device=DEV)
        LP = torch.zeros(ROLL, N, device=DEV); VL = torch.zeros(ROLL, N, device=DEV)
        RW = torch.zeros(ROLL, N, device=DEV); DN = torch.zeros(ROLL, N, device=DEV)
        for t in range(ROLL):
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
            s, n, sv = evalrun(net, use_carte); print("   %s it %3d | securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % (label, it, s, n, sv), flush=True)
    s, n, sv = evalrun(net, use_carte)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/commander_carte_%s.pt" % ("on" if use_carte else "off"))
    print(">>> %s FINI : securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % (label, s, n, sv), flush=True)
    return s, n, sv


if __name__ == "__main__":
    print("=== ABLATION CARTE (D=%d) : verite-terrain vs brouillard-memoire ===" % D, flush=True)
    off = train(False, "OFF verite ")
    on = train(True, "ON  carte  ")
    print("\n================= BILAN ABLATION (D=%d) =================" % D)
    print("  OFF (verite-terrain) : securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % off)
    print("  ON  (carte brouillard): securise %.0f%% | neutralise %.0f%% | survie %.0f%%" % on)
    print("  FOG TAX (securise)    : %+.0f points" % (on[0] - off[0]))
    print("  -> ON est la version DEPLOYABLE en Arma (pas de verite-terrain la-bas).")
