#!/usr/bin/env python3
"""reflex_goal_train.py — entraine R5 (locomotion-vers-but) sur reflex_goal_env. Metrique = ATTEINT LE BUT VIVANT.
A/B : voyant (sens du feu+couvert+but) vs aveugle (ne voit que le but) -> route-t-il par le couvert pour traverser ?"""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from reflex_goal_env import ReflexGoalEnv
from reflex_train import ReflexNet, act

DEV = "cuda:0"


@torch.no_grad()
def evaluate(net, blind, routed=False, n=4096, seed=999):
    e = ReflexGoalEnv(n, DEV, blind=blind, routed=routed, seed=seed); obs = e._obs(); rc = []; sv = []
    for _ in range(e.max_steps * 2):
        m, s, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(m, s)
        for i in torch.where(d > 0)[0].tolist(): rc.append(info["reached"][i].item()); sv.append(info["alive"][i].item())
    return 100.0 * sum(rc) / len(rc), 100.0 * sum(sv) / len(sv)


def train(blind, routed=False, iters=1000, envs=4096, T=24, lr=3e-4, h=128, tag="reflex"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.02
    env = ReflexGoalEnv(envs, DEV, blind=blind, routed=routed); O = env.obs_dim
    net = ReflexNet(O, env.D + 1, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("R5 %s | dev=%s N=%d O=%d" % ("AVEUGLE" if blind else "VOYANT", DEV, envs, O), flush=True)
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
        if it % 100 == 0 or it == iters - 1:
            rc, sv = evaluate(net, blind, routed)
            print("  it %4d | atteint le but %.0f%% | survie %.0f%% | %.0fs" % (it, rc, sv, time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s.pt" % tag)
    return evaluate(net, blind, routed)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=1000); p.add_argument("--envs", type=int, default=4096)
    a = p.parse_args()
    print("=== INTEGRATION : soldat SEUL (planifie le trajet) vs CHEF+SOLDAT (routeur + reflexe) ===", flush=True)
    rm, sm = train(blind=False, routed=False, iters=a.iters, envs=a.envs, tag="reflex_mono")
    rs, ss = train(blind=False, routed=True, iters=a.iters, envs=a.envs, tag="reflex_stack")
    print("\n=== RESULTAT ===", flush=True)
    print("SOLDAT SEUL (planifie le trajet)  : atteint le but %.0f%% | survie %.0f%%" % (rm, sm), flush=True)
    print("CHEF + SOLDAT (routeur + reflexe) : atteint le but %.0f%% | survie %.0f%%" % (rs, ss), flush=True)
    print("GAIN de la hierarchie : +%.0f pts d'atteinte" % (rs - rm), flush=True)
