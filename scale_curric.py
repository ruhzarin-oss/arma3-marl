import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV = "cuda:0"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def hit_sched(it, iters, lo=0.08, hi=0.16):
    f = it / iters
    if f < 0.30: return lo                      # facile : apprend a utiliser le couvert
    if f > 0.90: return hi                       # cible : consolide au dur
    return lo + (hi - lo) * (f - 0.30) / 0.60    # rampe


def train_curric(D=2, iters=200, envs=8192, rollout=16, seed=0, curric=True, hit_hi=0.16):
    torch.manual_seed(seed)                      # net + exploration reproductibles par graine
    env = AssaultTerrain(num_envs=envs, A=1, D=D, relief=40.0, hit=hit_hi, max_steps=60, device=DEV, seed=seed, shell_obs=True)
    net = Net(env.obs_dim, env.n_actions, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset(); rr = 0.0
    for it in range(iters):
        env.hit = hit_sched(it, iters, hi=hit_hi) if curric else hit_hi
        OB = torch.zeros(rollout, N0 := envs, 1, env.obs_dim, device=DEV); AC = torch.zeros(rollout, envs, 1, dtype=torch.long, device=DEV)
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


print("=== CURRICULUM D=2 cible h0.16 : taux de succes / 5 graines ===", flush=True)
for curric in [False, True]:
    sc = [train_curric(seed=s, curric=curric) for s in range(5)]
    succ = sum(1 for x in sc if x > 0.4)
    print(">>> curric=%s : scores=%s | succes %d/5" % (curric, [round(100*x) for x in sc], succ), flush=True)
print("CURRIC FINI", flush=True)
