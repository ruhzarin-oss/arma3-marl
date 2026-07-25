import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV = "cuda:0"
REPLICA = "/home/younes/arma3-marl/replica.npz"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def train_agent(net, opt, env, iters, rollout=16):
    envs = env.N
    env._reset(torch.arange(envs, device=DEV)); obs = env._obs(); rr = 0.0
    for it in range(iters):
        OB = torch.zeros(rollout, envs, 1, env.obs_dim, device=DEV); AC = torch.zeros(rollout, envs, 1, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, envs, 1, device=DEV); VL = torch.zeros(rollout, envs, device=DEV)
        RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        neut = nep = 0
        for t in range(rollout):
            with torch.no_grad():
                logits = net.a_logits(obs); dist = torch.distributions.Categorical(logits=logits)
                act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act)
            if rw.dim() > 1: rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done
            obs = nobs; dm = done.bool()
            if dm.any(): neut += info["neutralized"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        advA = adv.unsqueeze(-1).expand(rollout, envs, 1)
        ob = OB.reshape(-1, 1, env.obs_dim); ac = AC.reshape(-1, 1); oldlp = LP.reshape(-1, 1); advf = advA.reshape(-1, 1); retf = ret.reshape(-1)
        for ep in range(4):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits)
            lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            s1 = ratio * advf; s2 = torch.clamp(ratio, 0.8, 1.2) * advf; pl = -torch.min(s1, s2).mean()
            v = net.value(ob); vl = ((v - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = neut / max(nep, 1)
    return rr


P, K, G = 12, 30, 6
env = AssaultTerrain(num_envs=8192, A=1, D=2, relief=40.0, hit=0.16, max_steps=60, device=DEV, seed=0,
                     shell_obs=True, suffer=True, replica=True, replica_path=REPLICA)
O = env.obs_dim
torch.manual_seed(0)
nets = [Net(O, 10, 512, 3).to(DEV) for _ in range(P)]
opts = [torch.optim.Adam(n.parameters(), lr=3e-4) for n in nets]
print("=== PBT replica+suffer : P=%d K=%d G=%d (suffer plantait a 0/5 en PPO) ===" % (P, K, G), flush=True)
for gen in range(G):
    fits = [train_agent(nets[i], opts[i], env, K) for i in range(P)]
    order = sorted(range(P), key=lambda i: -fits[i])
    succ = sum(1 for f in fits if f > 0.4)
    print(">>> gen %d : best %.0f%% | moy %.0f%% | succes %d/%d" % (gen, 100*max(fits), 100*sum(fits)/P, succ, P), flush=True)
    elite = order[:P // 2]; losers = order[P // 2:]
    for li in losers:
        src = elite[torch.randint(0, len(elite), (1,)).item()]
        nets[li].load_state_dict(nets[src].state_dict())
        with torch.no_grad():
            for p in nets[li].parameters(): p.add_(0.02 * torch.randn_like(p))
        opts[li] = torch.optim.Adam(nets[li].parameters(), lr=3e-4)
print("PBT FINI", flush=True)
