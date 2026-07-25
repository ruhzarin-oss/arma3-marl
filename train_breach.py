"""BRECHE par CURRICULUM : D=1 (cible seule, flanc trivial) -> 3 -> 5, warm-start.
L'agent apprend a neutraliser SILENCIEUSEMENT le garde cible (approche angle mort + action 9), sans alarme."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from breach_env import BreachEnv
from train_koth_gpu import Net
DEV = "cuda:0"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def evalrun(net, D, sr, sj, envs=2048, steps=140, seed=999):
    env = BreachEnv(num_envs=envs, A=1, D=D, device=DEV, seed=seed, spawn_r=sr, spawn_jit_deg=sj); obs = env.reset()
    succ = alarm = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act); dm = done.bool()
            if dm.any():
                succ += info["success"][dm].float().sum().item(); alarm += info["alarm"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * succ / max(nep, 1), 100 * alarm / max(nep, 1)


def stage(net, opt, D, sr, sj, iters, envs=4096, rollout=24):
    env = BreachEnv(num_envs=envs, A=1, D=D, device=DEV, seed=0, spawn_r=sr, spawn_jit_deg=sj); O = env.obs_dim; obs = env.reset()
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
            loss = pl + 0.5 * vl - 0.02 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 40 == 0:
            u, a = evalrun(net, D, sr, sj); print("   D=%d r=%s jit=%d it %3d | NEUTRALISE SILENCIEUX %.0f%% | alarme %.0f%%" % (D, str(sr), sj, it, u, a), flush=True)
    return evalrun(net, D, sr, sj)


probe = BreachEnv(num_envs=1, A=1, D=1, device=DEV, seed=0, spawn_r=15.0, spawn_jit_deg=30.0)
net = Net(probe.obs_dim, probe.n_actions, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== CURRICULUM BRECHE (spawn dos->loin->aleatoire) obs_dim=%d ===" % probe.obs_dim, flush=True)
# (D gardes, spawn_r depuis la cible, jitter angulaire deg) : commence colle au dos, puis eloigne + randomise + densifie
STAGES = [(1, 15.0, 30.0), (1, 45.0, 90.0), (3, 80.0, 180.0), (5, 110.0, 180.0)]
for (D, sr, sj) in STAGES:
    u, a = stage(net, opt, D, sr, sj, iters=140)
    print(">>> PALIER D=%d r=%.0f jit=%.0f : NEUTRALISE SILENCIEUX %.0f%% | alarme %.0f%%" % (D, sr, sj, u, a), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/breach_d%d.pt" % D)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/breach.pt")
print("BREACH CURRIC FINI", flush=True)
