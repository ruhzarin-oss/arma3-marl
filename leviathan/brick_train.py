#!/usr/bin/env python3
"""brick_train.py — entraîneur PPO GÉNÉRIQUE pour les briques du répertoire. A/B voyant/aveugle.
Convention d'env : XxxEnv(n, device, blind, seed) ; .obs_dim ; .max_steps ; _obs() ; step(action_long)
-> (obs, reward, done, info) avec info[<metric>] = tensor bool/float par env (le succès).
Usage : python brick_train.py --env mod:Class --tag nom --metric clef --nact K [--iters 600 --envs 4096]"""
import argparse, importlib, time
import torch, torch.nn as nn
from torch.distributions import Categorical

DEV = "cuda:0"


class Net(nn.Module):
    def __init__(self, obs, nact, h=128):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.a = nn.Linear(h, nact); self.v = nn.Linear(h, 1)

    def forward(self, o):
        z = self.b(o); return self.a(z), self.v(z).squeeze(-1)


def act(net, obs, greedy=False):
    al, v = net(obs); d = Categorical(logits=al)
    a = al.argmax(-1) if greedy else d.sample()
    return a, d.log_prob(a), v


def load_env(spec):
    mod, cls = spec.split(":")
    return getattr(importlib.import_module(mod), cls)


@torch.no_grad()
def evaluate(EnvCls, net, blind, metric, n=4096, seed=999):
    e = EnvCls(n, DEV, blind=blind, seed=seed); obs = e._obs(); res = []
    for _ in range(e.max_steps * 2):
        a, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(a)
        for i in torch.where(d > 0)[0].tolist(): res.append(float(info[metric][i].item()))
    return 100.0 * sum(res) / max(1, len(res))


def train(EnvCls, blind, metric, nact, iters, envs, tag, T=26, lr=3e-4, h=128):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.03
    env = EnvCls(envs, DEV, blind=blind); O = env.obs_dim
    net = Net(O, nact, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr); obs = env._obs(); t0 = time.time()
    print("%s %s | O=%d nact=%d" % (tag, "AVEUGLE" if blind else "VOYANT", O, nact), flush=True)
    for it in range(iters):
        BO = torch.zeros(T, envs, O, device=DEV); BA = torch.zeros(T, envs, dtype=torch.long, device=DEV)
        BLP = torch.zeros(T, envs, device=DEV); BV = torch.zeros(T, envs, device=DEV)
        BR = torch.zeros(T, envs, device=DEV); BD = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            with torch.no_grad(): a, lp, v = act(net, obs)
            no, r, d, info = env.step(a); BO[t] = obs; BA[t] = a; BLP[t] = lp; BV[t] = v; BR[t] = r; BD[t] = d; obs = no
        with torch.no_grad(): _, _, lastv = act(net, obs)
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else BV[t + 1]; nt = 1 - BD[t]
            delta = BR[t] + gamma * nv * nt - BV[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); fa = BA.reshape(-1); fl = BLP.reshape(-1)
        for _ in range(epochs):
            al, val = net(fo); d = Categorical(logits=al); nlp = d.log_prob(fa); ratio = torch.exp(nlp - fl)
            pl = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = d.entropy().mean()
            loss = pl + vf * vl - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 150 == 0 or it == iters - 1:
            sv = evaluate(EnvCls, net, blind, metric)
            print("  it %4d | %s %.0f%% | %.0fs" % (it, metric, sv, time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s_%s.pt" % (tag, "aveugle" if blind else "voyant"))
    return evaluate(EnvCls, net, blind, metric)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--env", required=True); p.add_argument("--tag", required=True); p.add_argument("--metric", required=True)
    p.add_argument("--nact", type=int, required=True); p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=4096)
    a = p.parse_args(); E = load_env(a.env)
    print("=== BRIQUE %s (métrique=%s) ===" % (a.tag, a.metric), flush=True)
    sv = train(E, False, a.metric, a.nact, a.iters, a.envs, a.tag)
    bv = train(E, True, a.metric, a.nact, a.iters, a.envs, a.tag)
    print("\n=== %s : VOYANT %.0f%% | AVEUGLE %.0f%% | ÉCART +%.0f pts ===" % (a.tag, sv, bv, sv - bv), flush=True)
