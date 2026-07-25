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


def train(A, D, hit, iters=150, envs=8192, rollout=16, seed=0, **toggles):
    env = AssaultTerrain(num_envs=envs, A=A, D=D, relief=40.0, hit=hit, max_steps=60, device=DEV, seed=seed, **toggles)
    O, NA, N = env.obs_dim, env.n_actions, envs
    net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset(); rr = 0.0
    for it in range(iters):
        OB = torch.zeros(rollout, N, A, O, device=DEV); AC = torch.zeros(rollout, N, A, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, N, A, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
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
        advA = adv.unsqueeze(-1).expand(rollout, N, A)
        ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A); advf = advA.reshape(-1, A); retf = ret.reshape(-1)
        for ep in range(4):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits)
            lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            s1 = ratio * advf; s2 = torch.clamp(ratio, 0.8, 1.2) * advf; pl = -torch.min(s1, s2).mean()
            v = net.value(ob); vl = ((v - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = neut / max(nep, 1)
    return rr


# Profil de gain par sens, bande de forcage solo (D=2 hit=0.16), couvert TOUJOURS on.
A, D, hit = 1, 2, 0.16
ref = train(A, D, hit, shell_obs=True)
print(">>> REF coque seule : %.0f%%" % (100 * ref), flush=True)
for name, tog in [("+suffer", dict(shell_obs=True, suffer=True)),
                  ("+grille", dict(shell_obs=True, grid_obs=True))]:
    r = train(A, D, hit, **tog)
    print(">>> coque%s : %.0f%% | Δ %+.0f" % (name, 100 * r, 100 * (r - ref)), flush=True)
print("BLOCK FINI", flush=True)
