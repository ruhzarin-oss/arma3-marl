#!/usr/bin/env python3
"""suppression_train.py — apprend la SUPPRESSION (clouer l'ennemi pendant que l'ami manœuvre). PPO + A/B.
Voyant (voit l'expo de l'ami) doit supprimer AU BON MOMENT ; l'aveugle tire mal timé. Mesure = ami arrivé."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from suppression_env import SuppressionEnv

DEV = "cuda:0"


class SupNet(nn.Module):
    def __init__(self, obs, h=128):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mode = nn.Linear(h, 3); self.v = nn.Linear(h, 1)

    def forward(self, o):
        z = self.b(o); return self.mode(z), self.v(z).squeeze(-1)


def act(net, obs, greedy=False):
    ml, v = net(obs); dm = Categorical(logits=ml)
    m = ml.argmax(-1) if greedy else dm.sample()
    return m, dm.log_prob(m), v


@torch.no_grad()
def evaluate(net, blind, n=4096, seed=999):
    e = SuppressionEnv(n, DEV, blind=blind, seed=seed); obs = e._obs(); reached = []
    for _ in range(e.max_steps * 2):
        m, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(m)
        for i in torch.where(d > 0)[0].tolist(): reached.append(info["reached"][i].item())
    return 100.0 * sum(reached) / max(1, len(reached))


def train(blind, iters=600, envs=4096, T=24, lr=3e-4, h=128, tag="suppression"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.03
    env = SuppressionEnv(envs, DEV, blind=blind); O = env.obs_dim
    net = SupNet(O, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("SUPPRESSION %s | dev=%s N=%d O=%d" % ("AVEUGLE" if blind else "VOYANT", DEV, envs, O), flush=True)
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
        if it % 150 == 0 or it == iters - 1:
            sv = evaluate(net, blind); print("  it %4d | ami arrivé %.0f%% | %.0fs" % (it, sv, time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s.pt" % tag)
    return evaluate(net, blind)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=4096)
    a = p.parse_args()
    print("=== BRIQUE SUPPRESSION : clouer l'ennemi pour couvrir la manœuvre de l'ami ===", flush=True)
    sv = train(blind=False, iters=a.iters, envs=a.envs, tag="suppression_voyant")
    bv = train(blind=True, iters=a.iters, envs=a.envs, tag="suppression_aveugle")
    print("\n=== RÉSULTAT ===", flush=True)
    print("VOYANT  ami arrivé %.0f%% | AVEUGLE %.0f%% | ÉCART +%.0f pts" % (sv, bv, sv - bv), flush=True)
