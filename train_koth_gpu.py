"""train_koth_gpu — KotH 3 camps, TOUT sur la 3090 : sim GPU (koth_gpu) + 3 gros cerveaux + PPO en MINI-LOTS.
Objectif : SATURER le GPU avec du travail utile, memoire bornee. 1 cerveau par camp. Metriques en tenseurs."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from koth_gpu import KothGPU

NAMES = ["BLU", "OPF", "IND"]


class Net(nn.Module):
    def __init__(self, O, nact, hidden=512, layers=3):
        super().__init__()
        body = []; din = O
        for _ in range(layers):
            body += [nn.Linear(din, hidden), nn.ReLU()]; din = hidden
        self.body = nn.Sequential(*body); self.pi = nn.Linear(hidden, nact); self.v = nn.Linear(hidden, 1)

    def a_logits(self, obs): return self.pi(self.body(obs))
    def value(self, obs): return self.v(self.body(obs)).squeeze(-1).mean(-1)


def ppo_mb(net, opt, B, lastv, cfg, dev, mb):
    b_rew, b_val, b_done = B["rew"], B["val"], B["done"]
    T, N = b_rew.shape
    adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
    gamma, lam = cfg["gamma"], cfg["gae"]
    for t in reversed(range(T)):
        nnt = 1 - b_done[t]; nv = lastv if t == T - 1 else b_val[t + 1]
        delta = b_rew[t] + gamma * nv * nnt - b_val[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
    A = B["act"].shape[2]; O = B["obs"].shape[3]; M = T * N
    ret = (adv + b_val).reshape(M); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(M)
    fo = B["obs"].reshape(M, A, O); fa = B["act"].reshape(M, A); fl = B["logp"].reshape(M, A)
    for _ in range(cfg["epochs"]):
        perm = torch.randperm(M, device=dev)
        for i in range(0, M, mb):
            idx = perm[i:i + mb]
            dist = Categorical(logits=net.a_logits(fo[idx])); ratio = torch.exp(dist.log_prob(fa[idx]) - fl[idx])
            a_ = advn[idx].unsqueeze(1)
            ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
            vloss = ((net.value(fo[idx]) - ret[idx]) ** 2).mean(); ent = dist.entropy().mean()
            loss = ploss + cfg["vf"] * vloss - cfg["ent"] * ent
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()


def train(iters=300, envs=32768, rollout=16, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2, epochs=4,
          vf=0.5, ent=0.01, hidden=512, layers=3, mb=131072, hit=0.15, kappa=0.12, tie_pen=0.15, seed=0, save="kothgpu",
          ammo=False, ammo_max=40.0, supp_cost=3.0, ammo_regen=8.0):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = KothGPU(num_envs=envs, hit=hit, kappa=kappa, tie_pen=tie_pen, ammo=ammo, ammo_max=ammo_max, supp_cost=supp_cost, ammo_regen=ammo_regen, device=dev, seed=seed)
    C, A, O, NA = env.C, env.A, env.obs_dim, env.n_actions; obs = env.reset(); N = envs
    nets = [Net(O, NA, hidden, layers).to(dev) for _ in range(C)]
    opts = [torch.optim.Adam(nets[c].parameters(), lr=lr) for c in range(C)]
    npar = sum(p.numel() for p in nets[0].parameters()); ot = list(obs); T = rollout
    win = [torch.zeros((), device=dev) for _ in range(C)]; decs = torch.zeros((), device=dev)
    secs = torch.zeros((), device=dev); donec = torch.zeros((), device=dev); occ_s = torch.zeros((), device=dev); occ_n = 0
    gstep = 0; t0 = time.time()
    print("KOTH-GPU | dev=%s | envs=%d (x%d=%d batailles) | net=%dx%d (%d params/cerveau) | mb=%d"
          % (dev, N, C, N * C, layers, hidden, npar, mb), flush=True)
    for it in range(iters):
        B = [dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                  logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                  val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev)) for _ in range(C)]
        for t in range(T):
            with torch.no_grad():
                acts = []
                for c in range(C):
                    dd = Categorical(logits=nets[c].a_logits(ot[c])); a = dd.sample()
                    B[c]["obs"][t] = ot[c]; B[c]["act"][t] = a; B[c]["logp"][t] = dd.log_prob(a); B[c]["val"][t] = nets[c].value(ot[c])
                    acts.append(a)
            nobs, rews, done, info = env.step(acts)
            for c in range(C):
                B[c]["rew"][t] = rews[c]; B[c]["done"][t] = done
            dm = done.bool(); donec += dm.sum(); decs += (info["decided"] & dm).sum(); secs += (info["secured"] & dm).sum()
            for c in range(C):
                win[c] += ((info["winner"] == c) & dm).sum()
            occ_s += info["occ"].sum(); occ_n += N; ot = list(nobs); gstep += N
        for c in range(C):
            with torch.no_grad():
                lv = nets[c].value(ot[c])
            ppo_mb(nets[c], opts[c], B[c], lv, cfg, dev, mb)
        if it % 10 == 0 or it == iters - 1:
            dc = donec.item(); dec = decs.item()
            wr = [(win[c].item() / dec) if dec > 0 else 0.0 for c in range(C)]
            print("it %4d | OCCUP %.2f | SECUR %.2f | %s=%.2f %s=%.2f %s=%.2f | decid %.2f | %.0f tr/s | GPUmem %.1fGo"
                  % (it, occ_s.item() / max(1, occ_n), (secs.item() / dc if dc else 0), NAMES[0], wr[0], NAMES[1], wr[1],
                     NAMES[2], wr[2], (dec / dc if dc else 0), gstep / (time.time() - t0), torch.cuda.max_memory_allocated() / 1e9), flush=True)
            for c in range(C): win[c].zero_()
            decs.zero_(); secs.zero_(); donec.zero_(); occ_s.zero_(); occ_n = 0
    print("[fini] %.0f tr/s moyen | GPUmem max %.1f Go" % (gstep / (time.time() - t0), torch.cuda.max_memory_allocated() / 1e9), flush=True)
    for c in range(C):
        torch.save(nets[c].state_dict(), "/home/younes/arma3-marl/%s_%s.pt" % (save, NAMES[c].lower()))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=300); p.add_argument("--envs", type=int, default=32768)
    p.add_argument("--rollout", type=int, default=16); p.add_argument("--hidden", type=int, default=512)
    p.add_argument("--layers", type=int, default=3); p.add_argument("--mb", type=int, default=131072)
    p.add_argument("--hit", type=float, default=0.15); p.add_argument("--kappa", type=float, default=0.12)
    p.add_argument("--tie_pen", type=float, default=0.15); p.add_argument("--seed", type=int, default=0)
    p.add_argument("--save", type=str, default="kothgpu")
    p.add_argument("--ammo", action="store_true"); p.add_argument("--ammo_max", type=float, default=40.0)
    p.add_argument("--supp_cost", type=float, default=3.0); p.add_argument("--ammo_regen", type=float, default=8.0)
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, rollout=a.rollout, hidden=a.hidden, layers=a.layers, mb=a.mb,
          hit=a.hit, kappa=a.kappa, tie_pen=a.tie_pen, seed=a.seed, save=a.save,
          ammo=a.ammo, ammo_max=a.ammo_max, supp_cost=a.supp_cost, ammo_regen=a.ammo_regen)
