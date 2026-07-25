"""FURTIVITE par CURRICULUM : D=2 -> 3 -> 4 -> 5 -> 6 gardes, warm-start a chaque palier.
Commencer ou l'infiltration EST possible (gros trous) -> l'agent apprend a atteindre INVU,
puis durcir -> le skill transfere. Obs fixe (23) independante de D -> warm-start propre."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from stealth_env import StealthEnv
from train_koth_gpu import Net
DEV = "cuda:0"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def evalrun(net, D, envs=2048, steps=160, seed=999):
    env = StealthEnv(num_envs=envs, A=1, D=D, device=DEV, seed=seed); obs = env.reset()
    succ = alarm = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act); dm = done.bool()
            if dm.any():
                succ += info["success"][dm].float().sum().item(); alarm += info["alarm"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * succ / max(nep, 1), 100 * alarm / max(nep, 1)


def stage(net, opt, D, iters, envs=4096, rollout=24):
    env = StealthEnv(num_envs=envs, A=1, D=D, device=DEV, seed=0); O = env.obs_dim; obs = env.reset()
    for it in range(iters):
        OB = torch.zeros(rollout, envs, 1, O, device=DEV); AC = torch.zeros(rollout, envs, 1, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, envs, 1, device=DEV); VL = torch.zeros(rollout, envs, device=DEV)
        RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                lg = net.a_logits(obs); dist = torch.distributions.Categorical(logits=lg); a = dist.sample(); lp = dist.log_prob(a); v = net.value(obs)
            nobs, rw, done, info = env.step(a)
            OB[t] = obs; AC[t] = a; LP[t] = lp; VL[t] = v; RW[t] = rw; DN[t] = done; obs = nobs
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6); advA = adv.unsqueeze(-1)
        ob = OB.reshape(-1, 1, O); ac = AC.reshape(-1, 1); oldlp = LP.reshape(-1, 1); af = advA.reshape(-1, 1); rf = ret.reshape(-1)
        for ep in range(4):
            lg = net.a_logits(ob); dist = torch.distributions.Categorical(logits=lg); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * af, torch.clamp(ratio, 0.8, 1.2) * af).mean(); vl = ((net.value(ob) - rf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 40 == 0:
            u, a = evalrun(net, D); print("   D=%d it %3d | atteint INVU %.0f%% | alarme %.0f%%" % (D, it, u, a), flush=True)
    return evalrun(net, D)


probe = StealthEnv(num_envs=1, A=1, D=2, device=DEV, seed=0)
net = Net(probe.obs_dim, probe.n_actions, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== CURRICULUM FURTIVITE : D=2 -> 6 (obs_dim=%d) ===" % probe.obs_dim, flush=True)
for D in [2, 3, 4, 5, 6]:
    u, a = stage(net, opt, D, iters=120)
    print(">>> PALIER D=%d : atteint INVU %.0f%% | alarme %.0f%%" % (D, u, a), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/stealth_d%d.pt" % D)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/stealth_curric.pt")
print("STEALTH CURRIC FINI", flush=True)
