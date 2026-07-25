"""Entraine le skill ESCORTE (mono-agent PPO) sur EscortEnv. Sortie : escort.pt (Net 29->10).
Baseline = escort passif (ne fait rien) -> mesure combien d'otages survivent SANS escorte."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from escort_env import EscortEnv
from train_koth_gpu import Net
DEV = "cuda:0"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def evalrun(net, D, envs=2048, steps=140, seed=999, passive=False):
    env = EscortEnv(num_envs=envs, A=1, D=D, device=DEV, seed=seed); obs = env.reset(); succ = nep = hd = 0
    with torch.no_grad():
        for _ in range(steps):
            if passive: act = torch.full((envs, 1), 8, dtype=torch.long, device=DEV)
            else: act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act); dm = done.bool()
            if dm.any(): succ += info["success"][dm].float().sum().item(); hd += info["hdead"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * succ / max(nep, 1), 100 * hd / max(nep, 1)


def train(iters=250, envs=4096, rollout=24, D=6, lr=3e-4):
    torch.manual_seed(0)
    env = EscortEnv(num_envs=envs, A=1, D=D, device=DEV, seed=0)
    O, NA = env.obs_dim, env.n_actions
    net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    bs, bh = evalrun(net, D, passive=True)
    print("BASELINE escort PASSIF (D=%d) : otage survit %.0f%% | otage tue %.0f%%" % (D, bs, bh), flush=True)
    obs = env.reset()
    for it in range(iters):
        OB = torch.zeros(rollout, envs, 1, O, device=DEV); AC = torch.zeros(rollout, envs, 1, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, envs, 1, device=DEV); VL = torch.zeros(rollout, envs, device=DEV)
        RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                logits = net.a_logits(obs); dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done; obs = nobs
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6); advA = adv.unsqueeze(-1)
        ob = OB.reshape(-1, 1, O); ac = AC.reshape(-1, 1); oldlp = LP.reshape(-1, 1); advf = advA.reshape(-1, 1); retf = ret.reshape(-1)
        for ep in range(4):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * advf, torch.clamp(ratio, 0.8, 1.2) * advf).mean(); vl = ((net.value(ob) - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 25 == 0 or it == iters - 1:
            s, h = evalrun(net, D)
            print("it %3d | ESCORTE : otage survit %.0f%% | otage tue %.0f%%" % (it, s, h), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/escort.pt")
    s6, _ = evalrun(net, 6); s9, _ = evalrun(net, 9)
    print(">>> FINAL escort : survie D=6 %.0f%% | D=9 %.0f%% -> escort.pt" % (s6, s9), flush=True)
    print("ESCORT FINI", flush=True)


train()
