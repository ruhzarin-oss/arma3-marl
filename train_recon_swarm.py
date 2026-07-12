"""SWARM RECON — MARL PPO a politique PARTAGEE (parametres partages, lot = N*K drones, recompense d'EQUIPE).
Curriculum sur la TAILLE du terrain (le mur du mono-drone). Ablation finale K=1 vs K=4 sur grand terrain.

Usage : python train_recon_swarm.py [iters] [probe]
"""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from recon_swarm_env import ReconSwarmEnv
DEV = "cuda:0"
ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 140
K = 4
STAGES = [(0.25, 6), (0.40, 12), (0.50, 18)]      # (taille_terrain, nb_cibles) ; K=4 drones
if len(sys.argv) > 2 and sys.argv[2] == "probe":
    STAGES = [(0.40, 12)]


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)

    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, B = rew.shape; adv = torch.zeros(T, B, device=rew.device); g = torch.zeros(B, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def mkenv(N, ff, k, T, seed): return ReconSwarmEnv(N, K=k, T=T, device=DEV, seed=seed, max_steps=55, field_frac=ff)


def evalrun(net, ff, k, T, envs=1536, steps=80, seed=999):
    e = mkenv(envs, ff, k, T, seed); obs = e.reset(); rf = nr = al = ct = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs.reshape(-1, e.obs_dim)); a = mu.view(envs, k, 2)
            obs, rew, done, info = e.step(a)
            if done.any():
                dm = done
                rf += info["recog_frac"][dm].sum().item(); nr += info["nrecog"][dm].sum().item()
                ct += info["contact_frac"][dm].sum().item()
                al += info["all"][dm].float().sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * rf / max(nep, 1), nr / max(nep, 1), 100 * al / max(nep, 1), 100 * ct / max(nep, 1)


probe = mkenv(2, 0.4, K, 12, 0); O = probe.obs_dim; AC = probe.act_dim
net = CNet(O, AC, 256).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== SWARM RECON : MARL PPO partage, K=%d, curriculum=%s (obs=%d act=%d) ===" % (K, STAGES, O, AC), flush=True)
N = 2048; rollout = 12; B = N * K
for (ff, T) in STAGES:
    env = mkenv(N, ff, K, T, 0); obs = env.reset()
    for it in range(ITERS):
        OB = torch.zeros(rollout, B, O, device=DEV); ACT = torch.zeros(rollout, B, AC, device=DEV)
        LP = torch.zeros(rollout, B, device=DEV); VL = torch.zeros(rollout, B, device=DEV)
        RW = torch.zeros(rollout, B, device=DEV); DN = torch.zeros(rollout, B, device=DEV)
        for t in range(rollout):
            ob = obs.reshape(B, O)
            with torch.no_grad():
                mu, v = net(ob); std = net.log_std.exp(); dist = torch.distributions.Normal(mu, std)
                a = dist.sample(); lp = dist.log_prob(a).sum(-1)
            nobs, rw, done, info = env.step(a.view(N, K, 2))
            rwB = rw.unsqueeze(1).expand(N, K).reshape(B)        # recompense d'equipe -> chaque drone
            dnB = done.float().unsqueeze(1).expand(N, K).reshape(B)
            OB[t] = ob; ACT[t] = a; LP[t] = lp; VL[t] = v; RW[t] = rwB; DN[t] = dnB
            env.reset_done(done); obs = env._obs()
        with torch.no_grad(): _, lastv = net(obs.reshape(B, O))
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
            idf, nrec, alld, ctc = evalrun(net, ff, K, T)
            print("   [ff=%.2f T=%d K=%d] it %3d | identifie %.0f%% (%.1f/%d) | tout %.0f%% | contacts %.0f%%"
                  % (ff, T, K, it, idf, nrec, T, alld, ctc), flush=True)
    idf, nrec, alld, ctc = evalrun(net, ff, K, T)
    print(">>> PALIER ff=%.2f T=%d K=%d | identifie %.0f%% (%.1f/%d) | tout-identifie %.0f%% | contacts %.0f%%"
          % (ff, T, K, idf, nrec, T, alld, ctc), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/recon_swarm_ff%02d.pt" % int(ff * 100))
torch.save(net.state_dict(), "/home/younes/compose-embodiment/recon_swarm.pt")
# --- ABLATION : meme politique, grand terrain, K=1 vs K=4 ---
print("--- ABLATION grand terrain (ff=0.40, T=12) : la coordination casse-t-elle le mur ? ---", flush=True)
for k in [1, 2, 4]:
    idf, nrec, alld, ctc = evalrun(net, 0.40, k, 12)
    print("   K=%d | identifie %.0f%% (%.1f/12) | tout %.0f%% | contacts %.0f%%" % (k, idf, nrec, alld, ctc), flush=True)
print("SWARM RECON FINI -> recon_swarm.pt", flush=True)
