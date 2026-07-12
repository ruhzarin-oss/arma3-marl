#!/usr/bin/env python3
"""reflex_train.py — entraine R1 (reaction au feu) sur reflex_env, avec A/B : soldat VOYANT (sens du feu+couvert) vs AVEUGLE.
PPO mono-agent, 2 tetes (deplacement 9 / posture 2). La preuve = l'ecart de survie voyant - aveugle (a la +97 du couvert)."""
import time, argparse, statistics as st
import torch, torch.nn as nn
from torch.distributions import Categorical
from reflex_env import ReflexEnv

DEV = "cuda:0"


class ReflexNet(nn.Module):
    def __init__(self, obs, nm=9, h=128):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mv = nn.Linear(h, nm); self.stc = nn.Linear(h, 2); self.v = nn.Linear(h, 1)

    def forward(self, o):
        z = self.b(o); return self.mv(z), self.stc(z), self.v(z).squeeze(-1)


def act(net, obs, greedy=False):
    ml, sl, v = net(obs); dm = Categorical(logits=ml); ds = Categorical(logits=sl)
    m = ml.argmax(-1) if greedy else dm.sample(); s = sl.argmax(-1) if greedy else ds.sample()
    return m, s, dm.log_prob(m) + ds.log_prob(s), v


@torch.no_grad()
def evaluate(net, blind, n=4096, seed=999):
    e = ReflexEnv(n, DEV, blind=blind, seed=seed); obs = e._obs(); al = []
    for _ in range(e.max_steps * 2):
        m, s, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(m, s)
        for i in torch.where(d > 0)[0].tolist(): al.append(info["alive"][i].item())
    return 100.0 * (sum(al) / len(al)) if al else 0.0


def train(blind, iters=300, envs=2048, T=24, lr=3e-4, h=128, tag="reflex"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.02
    env = ReflexEnv(envs, DEV, blind=blind); O = env.obs_dim
    net = ReflexNet(O, env.D + 1, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("R1 %s | dev=%s N=%d O=%d" % ("AVEUGLE" if blind else "VOYANT", DEV, envs, O), flush=True)
    for it in range(iters):
        BO = torch.zeros(T, envs, O, device=DEV); BM = torch.zeros(T, envs, dtype=torch.long, device=DEV)
        BS = torch.zeros(T, envs, dtype=torch.long, device=DEV); BLP = torch.zeros(T, envs, device=DEV)
        BV = torch.zeros(T, envs, device=DEV); BR = torch.zeros(T, envs, device=DEV); BD = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            with torch.no_grad(): m, s, lp, v = act(net, obs)
            no, r, d, info = env.step(m, s)
            BO[t] = obs; BM[t] = m; BS[t] = s; BLP[t] = lp; BV[t] = v; BR[t] = r; BD[t] = d; obs = no
        with torch.no_grad(): _, _, _, lastv = act(net, obs)
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else BV[t + 1]; nt = 1 - BD[t]
            delta = BR[t] + gamma * nv * nt - BV[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); fm = BM.reshape(-1); fs = BS.reshape(-1); fl = BLP.reshape(-1)
        for _ in range(epochs):
            ml, sl, val = net(fo); dm = Categorical(logits=ml); ds = Categorical(logits=sl)
            nlp = dm.log_prob(fm) + ds.log_prob(fs); ratio = torch.exp(nlp - fl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = (dm.entropy() + ds.entropy()).mean()
            loss = ploss + vf * vl - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 50 == 0 or it == iters - 1:
            print("  it %4d | survie %.0f%% | %.0fs" % (it, evaluate(net, blind), time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s.pt" % tag)
    return evaluate(net, blind)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=300); p.add_argument("--envs", type=int, default=2048)
    a = p.parse_args()
    print("=== BRIQUE 1 : R1 reaction au feu — A/B voyant vs aveugle ===", flush=True)
    sv = train(blind=False, iters=a.iters, envs=a.envs, tag="reflex_r1_voyant")
    bl = train(blind=True, iters=a.iters, envs=a.envs, tag="reflex_r1_aveugle")
    print("\n=== RESULTAT ===", flush=True)
    print("VOYANT (sens du feu + couvert) : survie %.0f%%" % sv, flush=True)
    print("AVEUGLE                        : survie %.0f%%" % bl, flush=True)
    print("ECART (la valeur du sens du feu) : +%.0f points" % (sv - bl), flush=True)
