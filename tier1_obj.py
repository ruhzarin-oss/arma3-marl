import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
CKPT = "/home/younes/compose-embodiment/hostage_squad_d6.pt"   # base = infil + recup (d6, 69%)
OUT = "/home/younes/compose-embodiment/hostage_squad_tier1.pt"
FF_MAX, EXF_MAX = 0.05, 0.03


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def sched(it):
    # OBJECTIF PAR OBJECTIF : on empile une competence a la fois.
    if it < 40:  return 0.0, 0.0, "BASE infil+recup"
    if it < 160: return 0.0, EXF_MAX * min(1.0, (it - 40) / 120.0), "OBJ-A exfil vivant"
    if it < 180: return 0.0, EXF_MAX, "OBJ-A consolide"
    if it < 320: return FF_MAX * min(1.0, (it - 180) / 140.0), EXF_MAX, "OBJ-B discipline de feu"
    return FF_MAX, EXF_MAX, "PLEIN (A+B)"


def train(iters=350, envs=4096, rollout=24, D=6):
    torch.manual_seed(0)
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=0)
    O, NA, A = env.obs_dim, env.n_actions, env.A
    net = Net(O, NA, 512, 3).to(DEV); net.load_state_dict(torch.load(CKPT, map_location=DEV))   # WARM-START base
    opt = torch.optim.Adam(net.parameters(), lr=5e-5)   # FINE-TUNING DOUX (politique deja a 99%)
    obs = env.reset(); rr = 0.0; last = ""
    for it in range(iters):
        ff, exf, lab = sched(it); env.ff_hit = ff; env.exfil_hit = exf
        if lab != last: print("--- %s (it %d) ---" % (lab, it), flush=True); last = lab
        OB = torch.zeros(rollout, envs, A, O, device=DEV); AC = torch.zeros(rollout, envs, A, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, envs, A, device=DEV); VL = torch.zeros(rollout, envs, device=DEV)
        RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        succ = nep = pick = wipe = hdead = 0
        for t in range(rollout):
            with torch.no_grad():
                logits = net.a_logits(obs); dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act); rwm = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rwm; DN[t] = done; obs = nobs; dm = done.bool()
            if dm.any():
                succ += info["success"][dm].float().sum().item(); pick += info["picked"][dm].float().sum().item()
                wipe += info["squad_wipe"][dm].float().sum().item(); hdead += info["hdead"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / adv.std().clamp(min=1.0); advA = adv.unsqueeze(-1).expand(rollout, envs, A)  # PLANCHER std=1 : ne jamais amplifier (sinon politique excellente detonee)
        ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A); advf = advA.reshape(-1, A); retf = ret.reshape(-1)
        for ep in range(2):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * advf, torch.clamp(ratio, 0.8, 1.2) * advf).mean(); vl = ((net.value(ob) - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.003 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = succ / max(nep, 1)
        if it % 20 == 0:
            print("  it %3d | ff %.3f exf %.3f | RESCOUSSE %.0f%% | pickup %.0f%% | OTAGE TUE %.0f%% | detruite %.0f%%" % (
                it, ff, exf, 100 * rr, 100 * pick / max(nep, 1), 100 * hdead / max(nep, 1), 100 * wipe / max(nep, 1)), flush=True)
    torch.save(net.state_dict(), OUT)
    print(">>> TIER 1 objectif-par-objectif final : RESCOUSSE %.0f%% a fragilite pleine" % (100 * rr), flush=True)
    print("TIER1 FINI", flush=True)


print("=== TIER 1 OBJECTIF PAR OBJECTIF : base -> exfil vivant -> discipline de feu ===", flush=True)
train()
