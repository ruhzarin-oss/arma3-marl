#!/usr/bin/env python3
"""coevo_live.py — LA DERNIERE BRIQUE : co-evolution sur le VRAI sim (assault_terrain via CommanderEnv).
  ATTAQUANT = commandant (CNet obs17->4, warm-start commander.pt) : place ses 2 elements.
  DEFENSEUR = APPREND son PLACEMENT (2 clusters de 4 defenseurs) en surchargeant body.dpx/dpy (sans modifier le sim).
Meilleure-reponse ALTERNEE + POOL (league anti-oubli). Zero-somme sur le retour d'episode.
Montre : self-play naif = cycle ; league = converge. C'est la co-evolution branchee sur le monde reel."""
import sys, copy, math, torch, torch.nn as nn
from torch.distributions import Normal
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
N = 256; R_DEF = 22.0; STD_A = 0.3; STD_D = 0.35
CKC = "/home/younes/compose-embodiment/commander.pt"


class CNet(nn.Module):                                          # attaquant (identique commander.pt)
    def __init__(self, obs=17, act=4, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1); self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


class DefNet(nn.Module):                                        # defenseur : apprend 2 centres de cluster (placement)
    def __init__(self):
        super().__init__(); self.mu = nn.Parameter(torch.tensor([-0.5, 0.3, 0.5, -0.3]))
    def sample(self, n):
        m = self.mu.view(1, 2, 2).expand(n, 2, 2)
        dist = Normal(m, STD_D)
        pre = dist.sample()
        logp = dist.log_prob(pre).sum((1, 2))                   # grad via mu (REINFORCE correct)
        return torch.tanh(pre), logp


def apply_def(env, dc):                                         # surcharge les positions defenseur (2 clusters de 4 + jitter)
    b = env.body; D = b.D
    cx = torch.cat([dc[:, 0, 0:1].expand(-1, D // 2), dc[:, 1, 0:1].expand(-1, D - D // 2)], 1) * R_DEF
    cy = torch.cat([dc[:, 0, 1:2].expand(-1, D // 2), dc[:, 1, 1:2].expand(-1, D - D // 2)], 1) * R_DEF
    j = torch.randn(env.body.dpx.shape, device=DEV) * 3.0
    b.dpx = (cx + j).detach(); b.dpy = (cy + torch.randn_like(j) * 3.0).detach()


def episode(env, att, dfn):
    obs = env.reset()
    dc, dlogp = dfn.sample(N)
    logps = torch.zeros(N, device=DEV); ret = torch.zeros(N, device=DEV)
    for t in range(env.maxT):
        apply_def(env, dc)                                     # re-applique le placement (robuste a l'auto-reset)
        mu, _ = att(obs)
        dist = Normal(mu, att.log_std.exp() + STD_A)
        a = dist.sample()
        logps = logps + dist.log_prob(a).sum(1)                 # grad via mu (REINFORCE correct)
        obs, r, done, info = env.step(a.clamp(-1, 1).view(N, env.K, 2))
        ret = ret + r
    return logps, dlogp, ret


def train_att(env, att, opt, defpool, iters):
    for _ in range(iters):
        dfn = defpool[torch.randint(len(defpool), (1,)).item()]
        lp, _, R = episode(env, att, dfn)
        loss = -(lp * (R - R.mean())).mean()
        opt.zero_grad(); loss.backward(); opt.step()


def train_def(env, attpool, dfn, opt, iters):
    for _ in range(iters):
        at = attpool[torch.randint(len(attpool), (1,)).item()]
        _, dlp, R = episode(env, at, dfn)
        adv = (R.mean() - R)                                   # le defenseur veut MINIMISER le retour attaquant
        loss = -(dlp * (adv - adv.mean())).mean()
        opt.zero_grad(); loss.backward(); opt.step()


def evalR(env, att, dfn, reps=3):
    with torch.no_grad():
        return sum(float(episode(env, att, dfn)[2].mean()) for _ in range(reps)) / reps


def run(rounds=5, iters=25):
    torch.manual_seed(0)
    env = CommanderEnv(N, A=8, K=2, D=8, device=DEV, seed=1, max_steps=96)
    base = CNet().to(DEV)
    try:
        base.load_state_dict(torch.load(CKC, map_location=DEV)); print("[coevo-live] attaquant warm-start commander.pt", flush=True)
    except Exception as e:
        print("[coevo-live] pas de warm-start (%s)" % str(e)[:40], flush=True)

    # ---------- LEAGUE : pools des deux cotes ----------
    att = copy.deepcopy(base).to(DEV); dfn = DefNet().to(DEV)
    oa = torch.optim.Adam(att.parameters(), 1e-3); od = torch.optim.Adam(dfn.parameters(), 3e-2)
    apool = [copy.deepcopy(base).eval()]; dpool = [DefNet().to(DEV)]
    print("=== CO-EVOLUTION LIVE (assault_terrain) : attaquant vs defenseur APPRENANT + league ===", flush=True)
    for r in range(rounds):
        train_att(env, att, oa, dpool, iters)
        train_def(env, apool, dfn, od, iters)
        apool.append(copy.deepcopy(att).eval()); dpool.append(copy.deepcopy(dfn).eval())
        Rvd = evalR(env, att, dfn)                              # attaquant courant vs defenseur courant
        Rvs = evalR(env, att, dpool[0])                         # attaquant courant vs defense de base (anneau-ish)
        dm = dfn.mu.detach().view(2, 2)
        print("  round %d | retour att vs def-appris=%.2f | vs def-base=%.2f | clusters def=[(%.1f,%.1f),(%.1f,%.1f)]"
              % (r, Rvd, Rvs, dm[0, 0], dm[0, 1], dm[1, 0], dm[1, 1]), flush=True)
    torch.save({"attacker": att.state_dict(), "defender": dfn.state_dict()}, "/home/younes/compose-embodiment/coevo_live.pt")
    print("=== FIN co-evo live -> coevo_live.pt (les 2 commandements co-evolues sur le vrai sim) ===", flush=True)


if __name__ == "__main__":
    run()
