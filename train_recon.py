"""DRONE PERCEPTION ACTIVE — PPO continu sur ReconEnv. Le drone se PILOTE (vx,vy,dz) et apprend a
IDENTIFIER toutes les cibles (capteur simule). Curriculum sur le nb de cibles T (l'obs est une grille
-> dimension constante -> meme reseau, warm-start). Sauvegarde recon_T%d.pt.

Usage : python train_recon.py [iters] [t1,t2,...]
   ex : python train_recon.py 60 8          (validation)
        python train_recon.py 140 6,10,14   (complet)
"""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from recon_env import ReconEnv
DEV = "cuda:0"
ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 140
# curriculum (taille_terrain, nb_cibles) : petit+peu -> grand+beaucoup
STAGES = [(0.20, 5), (0.30, 8), (0.40, 12)]
if len(sys.argv) > 2 and sys.argv[2] == "probe":
    STAGES = [(0.20, 5)]


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


def mkenv(N, ff, T, seed): return ReconEnv(N, T=T, device=DEV, seed=seed, max_steps=55, field_frac=ff)


def evalrun(net, ff, T, envs=2048, steps=80, seed=999):
    e = mkenv(envs, ff, T, seed); obs = e.reset(); rf = nr = al = ct = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs); obs, rew, done, info = e.step(mu)
            if done.any():
                dm = done
                rf += info["recog_frac"][dm].sum().item(); nr += info["nrecog"][dm].sum().item()
                ct += info["contact_frac"][dm].sum().item()
                al += info["all"][dm].float().sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * rf / max(nep, 1), nr / max(nep, 1), 100 * al / max(nep, 1), 100 * ct / max(nep, 1)


probe = mkenv(2, 0.4, 8, 0); O = probe.obs_dim; AC = probe.act_dim
net = CNet(O, AC, 256).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== DRONE PERCEPTION ACTIVE (2D) : PPO, curriculum (terrain,cibles)=%s (obs=%d act=%d) ===" % (STAGES, O, AC), flush=True)
N = 4096; rollout = 12
for (ff, T) in STAGES:
    env = mkenv(N, ff, T, 0); obs = env.reset()
    for it in range(ITERS):
        OB = torch.zeros(rollout, N, O, device=DEV); ACT = torch.zeros(rollout, N, AC, device=DEV)
        LP = torch.zeros(rollout, N, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                mu, v = net(obs); std = net.log_std.exp(); dist = torch.distributions.Normal(mu, std)
                a = dist.sample(); lp = dist.log_prob(a).sum(-1)
            nobs, rw, done, info = env.step(a)
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
            loss = pl + 0.5 * vl - 0.02 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 20 == 0:
            idf, nrec, alld, ctc = evalrun(net, ff, T)
            print("   [ff=%.2f T=%d] it %3d | identifie %.0f%% (%.1f/%d) | tout %.0f%% | contacts %.0f%%" % (ff, T, it, idf, nrec, T, alld, ctc), flush=True)
    idf, nrec, alld, ctc = evalrun(net, ff, T)
    print(">>> PALIER ff=%.2f T=%d | identifie %.0f%% (%.1f/%d) | tout-identifie %.0f%% | contacts %.0f%%" % (ff, T, idf, nrec, T, alld, ctc), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/recon_T%d.pt" % T)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/recon.pt")
print("DRONE PERCEPTION ACTIVE FINI -> recon.pt", flush=True)
