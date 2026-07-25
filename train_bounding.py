"""BOUNDING OVERWATCH / assaut dur — entraine une escouade de 8 a PERCER une defense en profondeur :
se couvrir (coque) + SUPPRIMER (base de feu qui cloue, action 9) + AVANCER + survivre (pertes penalisees).
AssaultTerrain (coque + conscience d'equipe + suffer). Curriculum D=6->8->10->12, warm-start.
Mesure : % defenseurs neutralises (percee) + % escouade survivante."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV = "cuda:0"; A = 8


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def mkenv(N, D, seed):
    return AssaultTerrain(num_envs=N, A=A, D=D, device=DEV, seed=seed, shell_obs=True, team_obs=True,
                          suffer=True, relief=35.0, fire_range=110.0, secure_r=25.0, max_steps=80)


def evalrun(net, D, envs=2048, steps=170, seed=999):
    env = mkenv(envs, D, seed); obs = env.reset()
    win = surv = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act, auto_reset=True); dm = done.bool()
            if dm.any():
                win += info["neutralized"][dm].float().sum().item()
                surv += (1.0 - info["losses"])[dm].sum().item(); nep += int(dm.sum())
    return 100 * win / max(nep, 1), 100 * surv / max(nep, 1)


probe = mkenv(2, 6, 0); O = probe.obs_dim
net = Net(O, probe.n_actions, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("=== BOUNDING OVERWATCH : curriculum D=6->12 (obs=%d, A=%d) ===" % (O, A), flush=True)
N = 4096; rollout = 24
for D in [6, 8, 10, 12]:
    env = mkenv(N, D, 0); obs = env.reset()
    for it in range(150):
        OB = torch.zeros(rollout, N, A, O, device=DEV); AC = torch.zeros(rollout, N, A, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, N, A, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                lg = net.a_logits(obs); dist = torch.distributions.Categorical(logits=lg); a = dist.sample(); lp = dist.log_prob(a); v = net.value(obs)
            nobs, rw, done, info = env.step(a, auto_reset=True)
            OB[t] = obs; AC[t] = a; LP[t] = lp; VL[t] = v; RW[t] = rw; DN[t] = done; obs = nobs
        with torch.no_grad(): lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A)
        af = adv.reshape(-1, 1).expand(-1, A); rf = ret.reshape(-1)
        for ep in range(4):
            lg = net.a_logits(ob); dist = torch.distributions.Categorical(logits=lg); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * af, torch.clamp(ratio, 0.8, 1.2) * af).mean(); vl = ((net.value(ob) - rf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 30 == 0:
            w, s = evalrun(net, D); print("   D=%d it %3d | percee %.0f%% | survie %.0f%%" % (D, it, w, s), flush=True)
    w, s = evalrun(net, D); print(">>> PALIER D=%d : percee %.0f%% | survie %.0f%%" % (D, w, s), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/bounding_d%d.pt" % D)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/bounding.pt")
print("BOUNDING FINI -> bounding.pt", flush=True)
