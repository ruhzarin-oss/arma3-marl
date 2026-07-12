"""PROGRAMME DE NUIT — balayage de la CARTE brouillard-memoire.
Baseline OFF (verite-terrain, borne haute) + ON pour plusieurs vitesses d'OUBLI T (section F : le seul
reglage a trancher). Mesure le FOG TAX par T et designe le meilleur reglage. Remplit la nuit + cale le
brouillard + sort un tableau. ON est la SEULE version deployable en Arma -> loi du +97.
Usage : python train_carte_sweep.py [iters=120] [N=2048] [D=8]
"""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"
ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 120
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
D = int(sys.argv[3]) if len(sys.argv) > 3 else 8
A, K, ROLL, MAXT = 8, 4, 12, 120
TS = [3.0, 6.0, 12.0, 24.0]                       # vitesses d'oubli a balayer (pas-haut)


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


def mkenv(n, seed, kw):
    return CommanderEnv(n, A=A, K=K, D=D, device=DEV, seed=seed, max_steps=MAXT, **kw)


def evalrun(net, kw, envs=2048, steps=16, seed=999):
    e = mkenv(envs, seed, kw); obs = e.reset(); sec = neu = surv = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs); a = mu.view(envs, K, 2)
            obs, rew, done, info = e.step(a)
            if done.any():
                dm = done
                sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / A)[dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1)


def train(label, kw, tag):
    torch.manual_seed(0)
    probe = mkenv(2, 0, kw); O = probe.obs_dim; AC = probe.act_dim
    net = CNet(O, AC, 256).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    print("--- %s (obs=%d, N=%d, D=%d, %d iters) ---" % (label, O, N, D, ITERS), flush=True)
    env = mkenv(N, 0, kw); obs = env.reset()
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
            s, n, sv = evalrun(net, kw); print("   %s it %3d | secu %.0f%% | neut %.0f%% | surv %.0f%%" % (label, it, s, n, sv), flush=True)
    s, n, sv = evalrun(net, kw)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/commander_carte_%s.pt" % tag)
    print(">>> %s FINI : secu %.0f%% | neut %.0f%% | surv %.0f%%" % (label, s, n, sv), flush=True)
    return s, n, sv


if __name__ == "__main__":
    print("=== PROGRAMME DE NUIT : balayage CARTE brouillard (D=%d) ===" % D, flush=True)
    res = []
    off = train("OFF verite-terrain", dict(use_carte=False), "off")
    res.append(("OFF verite", None, off))
    for T in TS:
        on = train("ON  carte T=%g" % T, dict(use_carte=True, carte_T=T), "on_T%g" % T)
        res.append(("ON  T=%g" % T, T, on))
    print("\n================= BILAN NUIT (D=%d, borne haute = OFF) =================" % D)
    for lab, T, (s, n, sv) in res:
        tax = "" if T is None else "  | fog tax %+.0f pts" % (s - off[0])
        print("  %-14s : secu %3.0f%% | neut %3.0f%% | surv %3.0f%%%s" % (lab, s, n, sv, tax))
    best = max([r for r in res if r[1] is not None], key=lambda r: r[2][0])
    print("  -> MEILLEUR brouillard : %s (secu %.0f%%, fog tax %+.0f pts)" % (best[0], best[2][0], best[2][0] - off[0]))
