"""Entraine la politique de DEPLACEMENT EN FORMATION (8 formations randomisees, slot-following).
PPO partage, valeur par agent. Mesure : erreur de slot moyenne (m, plus bas = plus serre) + % arrive en formation."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from formation_env import FormationEnv, NAMES
from train_koth_gpu import Net
DEV = "cuda:0"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, M = rew.shape; adv = torch.zeros(T, M, device=rew.device); g = torch.zeros(M, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def vpa(net, obs):
    return net.v(net.body(obs)).squeeze(-1)


def evalrun(net, envs=2048, steps=160, seed=777):
    env = FormationEnv(num_envs=envs, A=8, device=DEV, seed=seed); obs = env.reset()
    serr = 0.0; ns = 0; held = 0; nep = 0
    with torch.no_grad():
        for _ in range(steps):
            act = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(act)
            serr += info["slot_err"].mean().item(); ns += 1
            dm = done.bool()
            if dm.any(): held += info["held"][dm].float().sum().item(); nep += int(dm.sum())
    return serr / max(ns, 1), 100 * held / max(nep, 1)


def per_formation(net, envs=512, steps=160):
    out = {}
    for fi, nm in enumerate(NAMES):
        env = FormationEnv(num_envs=envs, A=8, device=DEV, seed=fi + 1); env.fidx[:] = fi; obs = env._obs()
        s = 0.0; ns = 0
        with torch.no_grad():
            for _ in range(steps):
                act = net.a_logits(obs).argmax(-1)
                obs, rw, done, info = env.step(act); s += info["slot_err"].mean().item(); ns += 1
                env.fidx[:] = fi
        out[nm] = s / ns
    return out


env = FormationEnv(num_envs=4096, A=8, device=DEV, seed=0); O = env.obs_dim; A = env.A; obs = env.reset()
net = Net(O, 9, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
N = 4096; rollout = 24
print("=== ENTRAINEMENT FORMATIONS (obs=%d, A=%d, 8 formations) ===" % (O, A), flush=True)
for it in range(420):
    OB = torch.zeros(rollout, N, A, O, device=DEV); AC = torch.zeros(rollout, N, A, dtype=torch.long, device=DEV)
    LP = torch.zeros(rollout, N, A, device=DEV); VL = torch.zeros(rollout, N, A, device=DEV)
    RW = torch.zeros(rollout, N, A, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
    for t in range(rollout):
        with torch.no_grad():
            lg = net.a_logits(obs); dist = torch.distributions.Categorical(logits=lg); a = dist.sample(); lp = dist.log_prob(a); v = vpa(net, obs)
        nobs, rw, done, info = env.step(a)
        OB[t] = obs; AC[t] = a; LP[t] = lp; VL[t] = v; RW[t] = rw; DN[t] = done; obs = nobs
    with torch.no_grad(): lastv = vpa(net, obs).reshape(-1)
    rw_f = RW.reshape(rollout, N * A); vl_f = VL.reshape(rollout, N * A); dn_f = DN[:, :, None].expand(-1, -1, A).reshape(rollout, N * A)
    adv = gae(rw_f, vl_f, dn_f, lastv); ret = adv + vl_f; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
    ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A)
    af = adv.reshape(rollout * N, A); rf = ret.reshape(rollout * N, A)
    for ep in range(4):
        lg = net.a_logits(ob); dist = torch.distributions.Categorical(logits=lg); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
        pl = -torch.min(ratio * af, torch.clamp(ratio, 0.8, 1.2) * af).mean(); vl = ((vpa(net, ob) - rf) ** 2).mean(); ent = dist.entropy().mean()
        loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
    if it % 30 == 0:
        se, hd = evalrun(net); print("it %3d | erreur slot moy %.1f m | arrive en formation %.0f%%" % (it, se, hd), flush=True)
torch.save(net.state_dict(), "/home/younes/compose-embodiment/formation.pt")
pf = per_formation(net)
print(">>> erreur de slot par formation (m) : " + " · ".join("%s %.1f" % (k, v) for k, v in pf.items()), flush=True)
print("FORMATION FINI -> formation.pt", flush=True)
