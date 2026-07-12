"""COMMANDANT + DRONE (le commandant ALLOUE) — PPO continu sur CommanderDroneEnv.
Observation partielle (fog avec memoire) ; la politique place K elements ET envoie le drone de reco.
Curriculum D=4->8->12. Sauvegarde commander_drone_d%d.pt.

ABLATION intégrée : à chaque palier, on évalue la MEME politique drone-ON (r=70) vs drone-OFF (r=0).
Si sécuriser chute drone-OFF -> la politique a APPRIS à dépendre du drone (preuve "il sait s'en servir").

Usage : python train_commander_drone.py [iters] [d1,d2,...]
   ex : python train_commander_drone.py 50 4         (rapide, validation)
        python train_commander_drone.py 180 4,8,12   (complet)
"""
import sys, math, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_drone_env import CommanderDroneEnv
DEV = "cuda:0"

ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 180
DLIST = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else "4,8,12".split(","))]


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


def mkenv(N, D, seed, drone_r=70.0):
    return CommanderDroneEnv(N, A=8, K=4, D=D, device=DEV, seed=seed, max_steps=120, drone_r=drone_r,
                             reveal_bonus=0.02)


def evalrun(net, D, drone_r, envs=2048, steps=18, seed=999):
    e = mkenv(envs, D, seed, drone_r=drone_r); obs = e.reset(); sec = neu = surv = kn = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs); a = mu.view(envs, e.K + 1, 2)
            obs, rew, done, info = e.step(a)
            if done.any():
                dm = done
                sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / 8)[dm].sum().item(); kn += (info["known"] / e.D)[dm].sum().item()
                nep += int(dm.sum()); e.reset_done(dm)
    f = lambda x: 100 * x / max(nep, 1)
    return f(sec), f(neu), f(surv), f(kn)


probe = mkenv(2, 8, 0); O = probe.obs_dim; AC = probe.act_dim; K = probe.K
net = CNet(O, AC, 256).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== COMMANDANT+DRONE : PPO continu, K=%d elements + drone, fog-memoire, D=%s (obs=%d act=%d) ==="
      % (K, DLIST, O, AC), flush=True)
N = 4096; rollout = 12
for D in DLIST:
    env = mkenv(N, D, 0); obs = env.reset()
    for it in range(ITERS):
        OB = torch.zeros(rollout, N, O, device=DEV); ACT = torch.zeros(rollout, N, AC, device=DEV)
        LP = torch.zeros(rollout, N, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                mu, v = net(obs); std = net.log_std.exp(); dist = torch.distributions.Normal(mu, std)
                a = dist.sample(); lp = dist.log_prob(a).sum(-1)
            nobs, rw, done, info = env.step(a.view(N, K + 1, 2))
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
        if it % 20 == 0:
            s_on, n, sv, kon = evalrun(net, D, drone_r=70.0)
            print("   D=%d it %3d | ON: securise %.0f%% neutr %.0f%% survie %.0f%% connu %.0f%%"
                  % (D, it, s_on, n, sv, kon), flush=True)
    # --- palier : ABLATION drone ON vs OFF (meme politique) ---
    s_on, n_on, sv_on, k_on = evalrun(net, D, drone_r=70.0)
    s_off, n_off, sv_off, k_off = evalrun(net, D, drone_r=0.0)
    print(">>> PALIER D=%d | DRONE-ON securise %.0f%% (connu %.0f%%) | DRONE-OFF securise %.0f%% (connu %.0f%%) | GAIN DRONE = %+.0f pts"
          % (D, s_on, k_on, s_off, k_off, s_on - s_off), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/commander_drone_d%d.pt" % D)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/commander_drone.pt")
print("COMMANDANT+DRONE FINI -> commander_drone.pt", flush=True)
