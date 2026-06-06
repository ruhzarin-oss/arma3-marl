"""train_manager — MANAGER APPRIS [pile 1/5]. Un reseau qui CHOISIT objectif+posture par escouade,
a l'echelle operationnelle (toutes les K etapes), entraine par PPO dans le sim op_gpu (workers geles).
Baseline a battre : partition scriptee = 72 % militaire (validee). Politique 8 tetes (4 objectifs x 8 + 4
postures x 4) sur tronc partage. Recompense surtout terminale (anti reward-hacking) + leger shaping ennemi."""
import time, argparse, torch
import torch.nn as nn
from op_gpu import OpGPU, GOALS, STANCE_NAMES

p = argparse.ArgumentParser()
p.add_argument("--envs", type=int, default=8192); p.add_argument("--iters", type=int, default=300)
p.add_argument("--K", type=int, default=8, help="etapes du sim par decision du manager")
p.add_argument("--decisions", type=int, default=34, help="decisions du manager par episode")
p.add_argument("--lr", type=float, default=3e-4); p.add_argument("--save", type=str, default="manager.pt")
a = p.parse_args()
dev = "cuda:0"; torch.manual_seed(0)
S = 4; G = len(GOALS); ST = len(STANCE_NAMES)


class Manager(nn.Module):
    def __init__(self, obs_dim, h=128):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(obs_dim, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.goal_heads = nn.Linear(h, S * G)
        self.stance_heads = nn.Linear(h, S * ST)
        self.v = nn.Linear(h, 1)

    def forward(self, o):
        z = self.tr(o)
        gl = self.goal_heads(z).view(-1, S, G)
        sl = self.stance_heads(z).view(-1, S, ST)
        return gl, sl, self.v(z).squeeze(-1)


def policy(net, o, sample=True):
    gl, sl, v = net(o)
    gd = torch.distributions.Categorical(logits=gl); sd = torch.distributions.Categorical(logits=sl)
    if sample:
        g = gd.sample(); s = sd.sample()
    else:
        g = gl.argmax(-1); s = sl.argmax(-1)
    lp = gd.log_prob(g).sum(1) + sd.log_prob(s).sum(1)
    ent = gd.entropy().sum(1) + sd.entropy().sum(1)
    return g, s, lp, v, ent


def run_episode(net, env, K, decisions, train=True):
    N = env.N
    env._reset(torch.arange(N, device=dev))
    buf = {k: [] for k in ("obs", "g", "s", "lp", "v", "rew", "done")}
    en_tot = env.garr_hp0 + 2 * env.patrol_hp0 + env.qrf_hp0
    prev_en = (env.garr + env.patrol + env.qrf) / en_tot
    live = torch.ones(N, dtype=torch.bool, device=dev)
    term_mil = torch.zeros(N, device=dev); term_pertes = torch.zeros(N, device=dev)
    term_done = torch.zeros(N, dtype=torch.bool, device=dev)
    for di in range(decisions):
        o = env.obs()
        if train:
            g, s, lp, v, ent = policy(net, o, sample=True)
        else:
            with torch.no_grad():
                g, s, lp, v, ent = policy(net, o, sample=False)
        rew = torch.zeros(N, device=dev); newly_done = torch.zeros(N, dtype=torch.bool, device=dev)
        for _ in range(K):
            done, info = env.step(g, s)
            nd = done & live & ~newly_done
            if nd.any():
                r = info["mil"][nd].float() * 1.0 + (1 - info["pertes"][nd]).clamp(min=0) * 0.3
                r = r - (info["pertes"][nd] > 0.7).float() * 0.5
                rew[nd] = rew[nd] + r
                term_mil[nd] = info["mil"][nd].float(); term_pertes[nd] = info["pertes"][nd]
                term_done[nd] = True
                newly_done = newly_done | nd
        en_now = (env.garr + env.patrol + env.qrf) / en_tot
        rew = rew + (prev_en - en_now).clamp(min=0) * 0.3 * live.float()
        prev_en = en_now
        if train:
            buf["obs"].append(o); buf["g"].append(g); buf["s"].append(s)
            buf["lp"].append(lp.detach()); buf["v"].append(v.detach()); buf["rew"].append(rew)
            buf["done"].append((~live | newly_done).float())
        live = live & ~newly_done
        if not live.any(): break
    metrics = {"mil": term_mil[term_done].mean().item() if term_done.any() else 0.0,
               "pertes": term_pertes[term_done].mean().item() if term_done.any() else 0.0,
               "fini": term_done.float().mean().item()}
    return buf, metrics


GAMMA, LAM, CLIP, EPOCHS, MB = 0.99, 0.95, 0.2, 4, 16384
net = Manager(OpGPU(num_envs=2, device=dev).obs_dim()).to(dev)
opt = torch.optim.Adam(net.parameters(), lr=a.lr)
env = OpGPU(num_envs=a.envs, device=dev, seed=0)
print("MANAGER | envs=%d K=%d decisions=%d | baseline a battre : 72%% militaire" % (a.envs, a.K, a.decisions), flush=True)
t0 = time.time()
for it in range(a.iters):
    buf, m = run_episode(net, env, a.K, a.decisions, train=True)
    T = len(buf["obs"]); N = a.envs
    obs = torch.stack(buf["obs"]); g = torch.stack(buf["g"]); s = torch.stack(buf["s"])
    lp = torch.stack(buf["lp"]); val = torch.stack(buf["v"]); rew = torch.stack(buf["rew"]); dn = torch.stack(buf["done"])
    adv = torch.zeros(T, N, device=dev); gae = torch.zeros(N, device=dev)
    for t in reversed(range(T)):
        nxt = val[t + 1] if t + 1 < T else torch.zeros(N, device=dev)
        nd = 1.0 - dn[t]
        delta = rew[t] + GAMMA * nxt * nd - val[t]
        gae = delta + GAMMA * LAM * nd * gae
        adv[t] = gae
    ret = adv + val
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    of = obs.reshape(T * N, -1); gf = g.reshape(T * N, S); sf = s.reshape(T * N, S)
    lpf = lp.reshape(T * N); af = adv.reshape(T * N); rf = ret.reshape(T * N)
    for _ in range(EPOCHS):
        perm = torch.randperm(T * N, device=dev)
        for k in range(0, T * N, MB):
            mb = perm[k:k + MB]
            gl, sl, v = net(of[mb])
            gd = torch.distributions.Categorical(logits=gl); sd = torch.distributions.Categorical(logits=sl)
            lp2 = gd.log_prob(gf[mb]).sum(1) + sd.log_prob(sf[mb]).sum(1)
            ratio = (lp2 - lpf[mb]).exp(); A = af[mb]
            l_pi = -torch.min(ratio * A, ratio.clamp(1 - CLIP, 1 + CLIP) * A).mean()
            l_v = 0.5 * (v - rf[mb]).pow(2).mean()
            l_e = -0.01 * (gd.entropy().sum(1) + sd.entropy().sum(1)).mean()
            opt.zero_grad(); (l_pi + l_v + l_e).backward()
            nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
    if it % 20 == 0 or it == a.iters - 1:
        with torch.no_grad():
            _, me = run_episode(net, OpGPU(num_envs=4096, device=dev, seed=999), a.K, a.decisions, train=False)
        print("it %3d | militaire %.1f%% (eval) | pertes %.0f%% | %.0fs"
              % (it, 100 * me["mil"], 100 * me["pertes"], time.time() - t0), flush=True)
torch.save(net.state_dict(), a.save)
with torch.no_grad():
    _, mf = run_episode(net, OpGPU(num_envs=8192, device=dev, seed=12345), a.K, a.decisions, train=False)
print("[FINAL seed12345] manager militaire %.1f%% vs scripte 72%% | pertes %.0f%% | -> %s"
      % (100 * mf["mil"], 100 * mf["pertes"], a.save), flush=True)
