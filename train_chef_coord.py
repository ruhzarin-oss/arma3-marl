"""LE CHEF COORDONNE (commandant CENTRALISE). 1 politique voit toute la scene et sort, par pas :
  - UN axe d'avance commun (dir 0-7) -> les ASSAUT poussent ENSEMBLE (cohesion par construction)
  - un role/agent : APPUI (suppresse depuis sa position) / ASSAUT (avance sur l'axe).
Feu-et-mouvement articule. PPO sur le chef. On mesure rescousse + COHESION (faible dispersion = soude)."""
import sys, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
DEV = "cuda:0"


class Coord(nn.Module):
    def __init__(self, gdim, A, h=256):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(gdim, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.dirh = nn.Linear(h, 8); self.roleh = nn.Linear(h, A * 2); self.v = nn.Linear(h, 1); self.A = A

    def forward(self, o):
        z = self.tr(o)
        return self.dirh(z), self.roleh(z).view(-1, self.A, 2), self.v(z).squeeze(-1)


def gobs(env):
    N, S = env.N, env.S
    ag = torch.stack([env.B.apx / S, env.B.apy / S, env.B._aalive().float()], -1).reshape(N, -1)
    dg = torch.stack([env.B.dpx / S, env.B.dpy / S, env.B._dalive().float()], -1).reshape(N, -1)
    h = torch.stack([env.hpx / S, env.hpy / S, env.hdmg, env.picked], -1)
    e = torch.stack([env.extx / S, env.exty / S], -1)
    return torch.cat([ag, dg, h, e], -1)


def policy(net, o, sample=True):
    dl, rl, v = net(o)
    dd = torch.distributions.Categorical(logits=dl); rd = torch.distributions.Categorical(logits=rl)
    if sample:
        d = dd.sample(); r = rd.sample()
    else:
        d = dl.argmax(-1); r = rl.argmax(-1)
    lp = dd.log_prob(d) + rd.log_prob(r).sum(1)
    ent = dd.entropy() + rd.entropy().sum(1)
    return d, r, lp, v, ent


def act_from(d, r):                       # ASSAUT(r=1)->avance dir commun ; APPUI(r=0)->suppress(9)
    return torch.where(r == 1, d[:, None].expand_as(r), torch.full_like(r, 9))


def cohesion(env):                        # dispersion moyenne de l'escouade vivante (faible = soude)
    al = env.B._aalive().float(); n = al.sum(1).clamp(min=1)
    cx = (env.B.apx * al).sum(1) / n; cy = (env.B.apy * al).sum(1) / n
    d = torch.sqrt((env.B.apx - cx[:, None]) ** 2 + (env.B.apy - cy[:, None]) ** 2) * al
    return (d.sum(1) / n / env.S)


def sdobj(env):                           # distance du CENTROIDE de l'escouade a l'objectif courant
    al = env.B._aalive().float(); n = al.sum(1).clamp(min=1)
    cx = (env.B.apx * al).sum(1) / n; cy = (env.B.apy * al).sum(1) / n
    pk = (env.picked > 0.5)
    ox = torch.where(pk, env.extx, env.hpx); oy = torch.where(pk, env.exty, env.hpy)
    return torch.sqrt((cx - ox) ** 2 + (cy - oy) ** 2)


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape; adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nt = 1.0 - done[t]
        delta = rew[t] + gam * nv * nt - val[t]; g = delta + gam * lam * nt * g; adv[t] = g
    return adv


def train(iters=300, envs=4096, rollout=24, D=6, lr=3e-4):
    torch.manual_seed(0)
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=0); env.ff_hit = 0.0; env.exfil_hit = 0.0
    A = env.A; gdim = gobs(env).shape[-1]
    net = Coord(gdim, A).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env.reset()
    for it in range(iters):
        env.ff_hit = 0.0; env.exfil_hit = 0.0
        OB = torch.zeros(rollout, envs, gdim, device=DEV); DI = torch.zeros(rollout, envs, dtype=torch.long, device=DEV)
        RO = torch.zeros(rollout, envs, A, dtype=torch.long, device=DEV); LP = torch.zeros(rollout, envs, device=DEV)
        VL = torch.zeros(rollout, envs, device=DEV); RW = torch.zeros(rollout, envs, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        succ = nep = pick = wipe = 0; coh = 0.0
        for t in range(rollout):
            go = gobs(env)
            with torch.no_grad():
                d, r, lp, v, _ = policy(net, go, True)
            db = sdobj(env); pb = env.picked.clone()
            _, rw, done, info = env.step(act_from(d, r))
            da = sdobj(env); nd = 1.0 - done.float()
            prog = (db - da) / env.S * nd                                   # AVANCE du centroide vers l'objectif
            newpick = ((env.picked > 0.5) & (pb < 0.5)).float()
            rwm = 1.5 * prog + 3.0 * newpick + 12.0 * info["success"].float() - 0.5 * info["squad_wipe"].float() - 0.01
            OB[t] = go; DI[t] = d; RO[t] = r; LP[t] = lp; VL[t] = v; RW[t] = rwm; DN[t] = done
            coh += cohesion(env).mean().item(); dm = done.bool()
            if dm.any():
                succ += info["success"][dm].float().sum().item(); pick += info["picked"][dm].float().sum().item()
                wipe += info["squad_wipe"][dm].float().sum().item(); nep += int(dm.sum())
        with torch.no_grad(): lastv = policy(net, gobs(env), False)[3]
        adv = gae(RW, VL, DN, lastv); ret = adv + VL; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        ofb = OB.reshape(-1, gdim); dfb = DI.reshape(-1); rfb = RO.reshape(-1, A); lpf = LP.reshape(-1); af = adv.reshape(-1); rtf = ret.reshape(-1)
        for ep in range(4):
            dl, rl, v = net(ofb); dd = torch.distributions.Categorical(logits=dl); rd = torch.distributions.Categorical(logits=rl)
            lp2 = dd.log_prob(dfb) + rd.log_prob(rfb).sum(1); ratio = (lp2 - lpf).exp()
            pl = -torch.min(ratio * af, ratio.clamp(0.8, 1.2) * af).mean(); vl = ((v - rtf) ** 2).mean()
            ent = (dd.entropy() + rd.entropy().sum(1)).mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 20 == 0 or it == iters - 1:
            print("it %3d | RESCOUSSE %.0f%% | pickup %.0f%% | aneantie %.0f%% | cohesion %.3f" % (
                it, 100 * succ / max(nep, 1), 100 * pick / max(nep, 1), 100 * wipe / max(nep, 1), coh / rollout), flush=True)
    torch.save(net.state_dict(), "/home/younes/compose-embodiment/chef_coord.pt")
    print("CHEF COORD FINI -> chef_coord.pt", flush=True)


print("=== CHEF COORDONNE (centralise) : axe commun + appui/assaut ===", flush=True)
train()
