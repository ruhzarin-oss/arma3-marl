"""Entraine la FURTIVITE (mono-agent PPO) sur StealthEnv -> stealth.pt.
Baseline = foncer tout droit (mesure combien se font reperer). Cible : atteindre l'objectif NON DETECTE."""
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


def evalrun(net, envs=2048, steps=160, seed=999, rush=False):
    env = StealthEnv(num_envs=envs, A=1, D=6, device=DEV, seed=seed); obs = env.reset()
    reach = undet_reach = alarm = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            if rush:                                                       # foncer vers le centre (cap le + proche)
                ax = env.B.apx[:, 0]; ay = env.B.apy[:, 0]
                ang = torch.atan2(-ax, -ay); act = (torch.round(ang / (3.14159 / 4)) % 8).long().unsqueeze(1)
            else:
                act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act); dm = done.bool()
            if dm.any():
                reach += info["reached"][dm].float().sum().item(); alarm += info["alarm"][dm].float().sum().item()
                undet_reach += info["success"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * undet_reach / max(nep, 1), 100 * alarm / max(nep, 1)


def train(iters=250, envs=4096, rollout=24, lr=3e-4):
    torch.manual_seed(0)
    env = StealthEnv(num_envs=envs, A=1, D=6, device=DEV, seed=0)
    O, NA = env.obs_dim, env.n_actions
    net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    bu, ba = evalrun(net, rush=True)
    print("BASELINE foncer-tout-droit : atteint NON-DETECTE %.0f%% | alarme %.0f%%" % (bu, ba), flush=True)
    obs = env.reset()
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
        if it % 25 == 0 or it == iters - 1:
            u, a = evalrun(net)
            print("it %3d | FURTIF : atteint NON-DETECTE %.0f%% | alarme %.0f%%" % (it, u, a), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/stealth.pt")
    print("STEALTH FINI -> stealth.pt", flush=True)


train()
