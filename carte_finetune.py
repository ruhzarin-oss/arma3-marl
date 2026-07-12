"""FINE-TUNE ON — repart du commandant entraine (commander_k4_d8.pt) et l'adapte a la CARTE brouillard
(use_carte, T=6). But : fermer le fog tax (-7 pts zero-shot) -> le commandant qui LIT LA CARTE, deployable
en Arma. Warm-start => pas d'effondrement (il securise deja). Sortie : commander_carte_on.pt.
Usage : python carte_finetune.py [iters=60] [N=2048] [T=6]
"""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"; A, K, D, ROLL, MAXT = 8, 4, 8, 12, 120
ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
T = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
CKPT = "/home/younes/compose-embodiment/commander_k4_d8.pt"
OUT = "/home/younes/compose-embodiment/commander_carte_on.pt"


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)

    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    Tt, Nn = rew.shape; adv = torch.zeros(Tt, Nn, device=rew.device); g = torch.zeros(Nn, device=rew.device)
    for t in reversed(range(Tt)):
        nv = lastv if t == Tt - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def mkenv(n, seed, kw): return CommanderEnv(n, A=A, K=K, D=D, device=DEV, seed=seed, max_steps=MAXT, **kw)


def _eval1(net, kw, envs, steps, seed):
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


def evalrun(net, kw, envs=2048, steps=16, seeds=(777, 888, 999)):   # moyenne multi-seed = chiffre FIABLE
    rs = [_eval1(net, kw, envs, steps, s) for s in seeds]
    return tuple(sum(r[i] for r in rs) / len(rs) for i in range(3))


ON = dict(use_carte=True, carte_T=T); OFF = dict(use_carte=False)
probe = mkenv(2, 0, ON); O = probe.obs_dim; AC = probe.act_dim
net = CNet(O, AC, 256).to(DEV); net.load_state_dict(torch.load(CKPT, map_location=DEV))
opt = torch.optim.Adam(net.parameters(), lr=5e-5)              # lr TRES doux (stabilite warm-start)
print("=== FINE-TUNE ON carte (T=%g, D=%d, %d iters) depuis commander_k4_d8 ===" % (T, D, ITERS), flush=True)
ref = evalrun(net, OFF)[0]
print("   repere OFF (verite) = %.0f%% securise | depart ON = %.0f%%" % (ref, evalrun(net, ON)[0]), flush=True)
import copy
best_s = -1.0; best_state = copy.deepcopy(net.state_dict())     # on garde le MEILLEUR, pas le dernier
env = mkenv(N, 0, ON); obs = env.reset()
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
    if it % 5 == 0 or it == ITERS - 1:
        s, n, sv = evalrun(net, ON)
        flag = ""
        if s > best_s:
            best_s = s; best_state = copy.deepcopy(net.state_dict()); flag = "  <- meilleur"
        print("   it %3d | ON secu %.0f%% | neut %.0f%% | surv %.0f%% | tax vs OFF %+.0f%s" % (it, s, n, sv, s - ref, flag), flush=True)
torch.save(best_state, OUT)                                     # on sauve le MEILLEUR
print(">>> FINI : MEILLEUR ON carte %.0f%% securise (repere OFF %.0f%%, tax %+.0f pts) -> %s" % (best_s, ref, best_s - ref, OUT), flush=True)
