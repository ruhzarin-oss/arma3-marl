import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
CKPT = "/home/younes/compose-embodiment/hostage_squad.pt"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def greedy_eval(net, D=3, envs=1024, steps=160, seed=999):
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=seed); obs = env.reset()
    succ = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act); dm = done.bool()
            if dm.any(): succ += info["success"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * succ / max(nep, 1)


def train(iters=200, envs=4096, rollout=24, D=3, ent_coef=0.003):
    torch.manual_seed(0)
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=0)
    O, NA, A = env.obs_dim, env.n_actions, env.A
    net = Net(O, NA, 512, 3).to(DEV); net.load_state_dict(torch.load(CKPT, map_location=DEV))   # WARM-START
    opt = torch.optim.Adam(net.parameters(), lr=2e-4)
    obs = env.reset()
    print("greedy AVANT crispen : %.0f%%" % greedy_eval(net), flush=True)
    for it in range(iters):
        OB = torch.zeros(rollout, envs, A, O, device=DEV); AC = torch.zeros(rollout, envs, A, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, envs, A, device=DEV); VL = torch.zeros(rollout, envs, device=DEV)
        RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        succ = nep = 0
        for t in range(rollout):
            with torch.no_grad():
                logits = net.a_logits(obs); dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act); rwm = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rwm; DN[t] = done; obs = nobs; dm = done.bool()
            if dm.any(): succ += info["success"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6); advA = adv.unsqueeze(-1).expand(rollout, envs, A)
        ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A); advf = advA.reshape(-1, A); retf = ret.reshape(-1)
        for ep in range(4):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * advf, torch.clamp(ratio, 0.8, 1.2) * advf).mean(); vl = ((net.value(ob) - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - ent_coef * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 30 == 0:
            print("  it %3d | echantillonne %.0f%% | GREEDY %.0f%%" % (it, 100 * succ / max(nep, 1), greedy_eval(net)), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/hostage_squad_v11.pt")
    print("greedy APRES crispen : %.0f%%" % greedy_eval(net), flush=True)
    print("CRISPEN FINI", flush=True)


print("=== CRISPEN : warm-start + entropie basse -> politique nette (greedy) ===", flush=True)
train()
