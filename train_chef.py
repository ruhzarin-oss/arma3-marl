"""train_chef — LE CHEF D'EQUIPE [hierarchique, calque sur train_manager.py].
Commandant APPRIS assigne un ROLE a chacun des 9 soldats toutes les K etapes. Soldats = d6 GELE.
Roles DISTINCTS sur d6 gele :
  APPUI(0)   = chasse le garde le plus proche (avance vers lui, suppresse a portee) -> nettoie
  ASSAUT(1)  = fonce l'objectif (cap direct otage/extraction, jamais suppress) -> perce
  PORTEUR(2) = d6 tel quel (se couvre, porte) -> defaut malin
PPO sur le seul chef -> d6 ne bouge pas, pas d'effondrement. Baseline = d6-solo (tout PORTEUR)."""
import sys, time, math, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
D6 = "/home/younes/compose-embodiment/hostage_v1_FINAL.pt"
NROLES = 3


class Chef(nn.Module):
    def __init__(self, gdim, A, h=256):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(gdim, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.role = nn.Linear(h, A * NROLES); self.v = nn.Linear(h, 1); self.A = A

    def forward(self, o):
        z = self.tr(o)
        return self.role(z).view(-1, self.A, NROLES), self.v(z).squeeze(-1)


def chef_obs(env):
    N, S = env.N, env.S
    ag = torch.stack([env.B.apx / S, env.B.apy / S, env.B._aalive().float()], -1).reshape(N, -1)
    dg = torch.stack([env.B.dpx / S, env.B.dpy / S, env.B._dalive().float()], -1).reshape(N, -1)
    h = torch.stack([env.hpx / S, env.hpy / S, env.hdmg, env.picked], -1)
    e = torch.stack([env.extx / S, env.exty / S], -1)
    return torch.cat([ag, dg, h, e], -1)


def cap_toward(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)) % 8).long()


def guard_info(env):
    ax, ay, S, N, A, D = env.B.apx, env.B.apy, env.S, env.N, env.A, env.D
    gpx, gpy, dal = env.B.dpx, env.B.dpy, env.B._dalive()
    dx = gpx[:, None, :] - ax[:, :, None]; dy = gpy[:, None, :] - ay[:, :, None]
    d2 = torch.where(dal[:, None, :], dx * dx + dy * dy, torch.full_like(dx, 1e18)); km = d2.argmin(2)
    ngx = torch.gather(gpx[:, None, :].expand(N, A, D), 2, km[..., None]).squeeze(2)
    ngy = torch.gather(gpy[:, None, :].expand(N, A, D), 2, km[..., None]).squeeze(2)
    gdx = ngx - ax; gdy = ngy - ay; gd = torch.sqrt(gdx ** 2 + gdy ** 2) + 1e-6
    los = env.B._losc(env.B.hm, ax, ay, ngx, ngy, S)
    inr = (los > 0.5) & (gd < env.fire_range) & dal.any(1, keepdim=True)
    return gdx, gdy, inr


def modulate(dact, roles, env):
    ax, ay = env.B.apx, env.B.apy
    gdx, gdy, inr = guard_info(env)
    act = dact.clone()
    appui = roles == 0; cap_g = cap_toward(gdx, gdy)
    act = torch.where(appui & inr, torch.full_like(act, 9), act)
    act = torch.where(appui & ~inr, cap_g, act)
    assaut = roles == 1; pk = (env.picked[:, None] > 0.5)
    tx = torch.where(pk, env.extx[:, None] - ax, env.hpx[:, None] - ax)
    ty = torch.where(pk, env.exty[:, None] - ay, env.hpy[:, None] - ay)
    act = torch.where(assaut, cap_toward(tx, ty), act)
    return act


def chef_policy(net, o, sample=True):
    rl, v = net(o); d = torch.distributions.Categorical(logits=rl)
    r = d.sample() if sample else rl.argmax(-1)
    return r, d.log_prob(r).sum(1), v, d.entropy().sum(1)


def rollout(chef, d6, env, K, decisions, train=True, fixed_role=None):
    N, A = env.N, env.A; obs = env.reset()
    buf = {k: [] for k in ("o", "r", "lp", "v", "rew", "dn")}
    succ = nep = pick = wipe = 0; rolecnt = torch.zeros(NROLES, device=DEV)
    for di in range(decisions):
        go = chef_obs(env)
        if fixed_role is not None:
            roles = torch.full((N, A), fixed_role, dtype=torch.long, device=DEV); lp = v = None
        elif train:
            roles, lp, v, _ = chef_policy(chef, go, True)
        else:
            with torch.no_grad(): roles, lp, v, _ = chef_policy(chef, go, False)
        rolecnt += torch.bincount(roles.reshape(-1), minlength=NROLES).float()
        racc = torch.zeros(N, device=DEV); dany = torch.zeros(N, dtype=torch.bool, device=DEV)
        for _ in range(K):
            with torch.no_grad():
                dact = torch.distributions.Categorical(logits=d6.a_logits(obs)).sample()
            act = modulate(dact, roles, env)
            obs, rw, done, info = env.step(act); racc = racc + rw.mean(-1); dm = done.bool(); dany |= dm
            if dm.any():
                succ += info["success"][dm].float().sum().item(); pick += info["picked"][dm].float().sum().item()
                wipe += info["squad_wipe"][dm].float().sum().item(); nep += int(dm.sum())
        if train and fixed_role is None:
            buf["o"].append(go); buf["r"].append(roles); buf["lp"].append(lp.detach()); buf["v"].append(v.detach()); buf["rew"].append(racc); buf["dn"].append(dany.float())
    m = {"resc": succ / max(nep, 1), "pick": pick / max(nep, 1), "wipe": wipe / max(nep, 1), "roles": (rolecnt / rolecnt.sum().clamp(min=1)).tolist()}
    return buf, m


def main(iters=150, envs=2048, K=6, decisions=20, D=8, lr=3e-4):
    torch.manual_seed(0)
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=0); env.ff_hit = 0.0; env.exfil_hit = 0.0
    O, NA, A = env.obs_dim, env.n_actions, env.A
    d6 = Net(O, NA, 512, 3).to(DEV); d6.load_state_dict(torch.load(D6, map_location=DEV)); d6.eval()
    for p in d6.parameters(): p.requires_grad_(False)
    gdim = chef_obs(env).shape[-1]
    chef = Chef(gdim, A).to(DEV); opt = torch.optim.Adam(chef.parameters(), lr=lr)
    _, b = rollout(chef, d6, HostageEnv(num_envs=2048, A=9, D=D, device=DEV, seed=999), K, decisions, train=False, fixed_role=2)
    print("BASELINE d6-solo (tout PORTEUR, D=%d) : RESCOUSSE %.0f%% | pickup %.0f%% | aneantie %.0f%%" % (D, 100 * b["resc"], 100 * b["pick"], 100 * b["wipe"]), flush=True)
    t0 = time.time()
    for it in range(iters):
        env.ff_hit = 0.0; env.exfil_hit = 0.0
        buf, m = rollout(chef, d6, env, K, decisions, train=True)
        T = len(buf["o"]); o = torch.stack(buf["o"]); r = torch.stack(buf["r"]); lp = torch.stack(buf["lp"]); val = torch.stack(buf["v"]); rew = torch.stack(buf["rew"]); dn = torch.stack(buf["dn"])
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nxt = val[t + 1] if t + 1 < T else torch.zeros(envs, device=DEV); nd = 1.0 - dn[t]
            delta = rew[t] + 0.99 * nxt * nd - val[t]; g = delta + 0.99 * 0.95 * nd * g; adv[t] = g
        ret = adv + val; adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        of = o.reshape(T * envs, -1); rf = r.reshape(T * envs, A); lpf = lp.reshape(T * envs); af = adv.reshape(T * envs); rtf = ret.reshape(T * envs)
        for _ in range(4):
            rl, v = chef(of); d = torch.distributions.Categorical(logits=rl); lp2 = d.log_prob(rf).sum(1); ratio = (lp2 - lpf).exp()
            l_pi = -torch.min(ratio * af, ratio.clamp(0.8, 1.2) * af).mean(); l_v = 0.5 * (v - rtf).pow(2).mean(); l_e = -0.01 * d.entropy().sum(1).mean()
            opt.zero_grad(); (l_pi + l_v + l_e).backward(); nn.utils.clip_grad_norm_(chef.parameters(), 0.5); opt.step()
        if it % 15 == 0 or it == iters - 1:
            with torch.no_grad():
                _, me = rollout(chef, d6, HostageEnv(num_envs=2048, A=9, D=D, device=DEV, seed=999), K, decisions, train=False)
            print("it %3d | CHEF resc %.0f%% pick %.0f%% aneantie %.0f%% | assaut/appui/porteur %.0f/%.0f/%.0f%% | %.0fs" % (
                it, 100 * me["resc"], 100 * me["pick"], 100 * me["wipe"], 100 * me["roles"][1], 100 * me["roles"][0], 100 * me["roles"][2], time.time() - t0), flush=True)
    torch.save(chef.state_dict(), "/home/younes/compose-embodiment/chef.pt")
    print("CHEF FINI -> chef.pt", flush=True)


main()
