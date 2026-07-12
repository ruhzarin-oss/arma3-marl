#!/usr/bin/env python3
"""reflex_travel_train.py — apprend la MARCHE vers un point (R5 calme). PPO + A/B voyant/aveugle.
Le voyant (sens des obstacles) doit contourner ; l'aveugle se coince. Sort reflex_travel_voyant.pt."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from reflex_travel_env import TravelEnv

DEV = "cuda:0"


class TravelNet(nn.Module):
    def __init__(self, obs, D=8, h=128):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mv = nn.Linear(h, D + 1); self.v = nn.Linear(h, 1)

    def forward(self, o):
        z = self.b(o); return self.mv(z), self.v(z).squeeze(-1)


def act(net, obs, greedy=False):
    ml, v = net(obs); dm = Categorical(logits=ml)
    m = ml.argmax(-1) if greedy else dm.sample()
    return m, dm.log_prob(m), v


@torch.no_grad()
def evaluate(net, blind, n=4096, seed=999):
    e = TravelEnv(n, DEV, blind=blind, seed=seed); obs = e._obs(); reached = []
    for _ in range(e.max_steps * 2):
        m, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(m)
        for i in torch.where(d > 0)[0].tolist(): reached.append(info["reached"][i].item())
    return 100.0 * sum(reached) / max(1, len(reached))


def train(blind, iters=600, envs=2048, T=24, lr=3e-4, h=128, tag="reflex_travel"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.02
    env = TravelEnv(envs, DEV, blind=blind); O = env.obs_dim; D = env.D
    net = TravelNet(O, D, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("TRAVEL %s | dev=%s N=%d O=%d" % ("AVEUGLE" if blind else "VOYANT", DEV, envs, O), flush=True)
    for it in range(iters):
        BO = torch.zeros(T, envs, O, device=DEV); BM = torch.zeros(T, envs, dtype=torch.long, device=DEV)
        BLP = torch.zeros(T, envs, device=DEV); BV = torch.zeros(T, envs, device=DEV)
        BR = torch.zeros(T, envs, device=DEV); BD = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            with torch.no_grad(): m, lp, v = act(net, obs)
            no, r, d, info = env.step(m)
            BO[t] = obs; BM[t] = m; BLP[t] = lp; BV[t] = v; BR[t] = r; BD[t] = d; obs = no
        with torch.no_grad(): _, _, lastv = act(net, obs)
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else BV[t + 1]; nt = 1 - BD[t]
            delta = BR[t] + gamma * nv * nt - BV[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); fm = BM.reshape(-1); fl = BLP.reshape(-1)
        for _ in range(epochs):
            ml, val = net(fo); dm = Categorical(logits=ml)
            nlp = dm.log_prob(fm); ratio = torch.exp(nlp - fl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = dm.entropy().mean()
            loss = ploss + vf * vl - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 100 == 0 or it == iters - 1:
            sv = evaluate(net, blind); print("  it %4d | arrivé %.0f%% | %.0fs" % (it, sv, time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s.pt" % tag)
    return evaluate(net, blind)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=2048)
    a = p.parse_args()
    print("=== R5 CALME : apprendre à VOYAGER (marcher vers un point, contourner les obstacles) ===", flush=True)
    sv = train(blind=False, iters=a.iters, envs=a.envs, tag="reflex_travel_voyant")
    bv = train(blind=True, iters=a.iters, envs=a.envs, tag="reflex_travel_aveugle")
    print("\n=== RÉSULTAT ===", flush=True)
    print("VOYANT  arrivé %.0f%%" % sv, flush=True)
    print("AVEUGLE arrivé %.0f%%" % bv, flush=True)
    print("ÉCART : +%.0f pts (le sens des obstacles paie pour le voyage)" % (sv - bv), flush=True)
