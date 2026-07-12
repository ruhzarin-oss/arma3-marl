#!/usr/bin/env python3
"""reflex_fight_train.py — R2 tir reactif VISE + R3 micro-couvert (peek-and-shoot). 3 tetes : deplacement / posture / FEU (secteur).
Viser exige le sens du feu -> l'aveugle tire dans le vide. Mesure survie ET tireurs neutralises. A/B voyant vs aveugle."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from reflex_fight_env import ReflexFightEnv

DEV = "cuda:0"


class FightNet(nn.Module):
    def __init__(self, obs, D=8, h=160):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mv = nn.Linear(h, D + 1); self.stc = nn.Linear(h, 2); self.fire = nn.Linear(h, D + 1); self.v = nn.Linear(h, 1)

    def forward(self, o):
        z = self.b(o); return self.mv(z), self.stc(z), self.fire(z), self.v(z).squeeze(-1)


def act(net, obs, greedy=False):
    ml, sl, fl, v = net(obs)
    dm = Categorical(logits=ml); ds = Categorical(logits=sl); df = Categorical(logits=fl)
    if greedy: m, s, f = ml.argmax(-1), sl.argmax(-1), fl.argmax(-1)
    else: m, s, f = dm.sample(), ds.sample(), df.sample()
    return m, s, f, dm.log_prob(m) + ds.log_prob(s) + df.log_prob(f), v


@torch.no_grad()
def evaluate(net, blind, n=4096, seed=999):
    e = ReflexFightEnv(n, DEV, blind=blind, seed=seed); obs = e._obs(); al = []; kl = []
    for _ in range(e.max_steps * 2):
        m, s, f, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(m, s, f)
        for i in torch.where(d > 0)[0].tolist(): al.append(info["alive"][i].item()); kl.append(info["killed"][i].item())
    return 100.0 * sum(al) / len(al), sum(kl) / len(kl), e.K


def train(blind, iters=1000, envs=4096, T=24, lr=3e-4, h=160, tag="reflex"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.03
    env = ReflexFightEnv(envs, DEV, blind=blind); O = env.obs_dim; D = env.D
    net = FightNet(O, D, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("R2/R3 %s | dev=%s N=%d O=%d" % ("AVEUGLE" if blind else "VOYANT", DEV, envs, O), flush=True)
    for it in range(iters):
        BO = torch.zeros(T, envs, O, device=DEV)
        BM = torch.zeros(T, envs, dtype=torch.long, device=DEV); BS = torch.zeros(T, envs, dtype=torch.long, device=DEV)
        BF = torch.zeros(T, envs, dtype=torch.long, device=DEV); BLP = torch.zeros(T, envs, device=DEV)
        BV = torch.zeros(T, envs, device=DEV); BR = torch.zeros(T, envs, device=DEV); BD = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            with torch.no_grad(): m, s, f, lp, v = act(net, obs)
            no, r, d, info = env.step(m, s, f)
            BO[t] = obs; BM[t] = m; BS[t] = s; BF[t] = f; BLP[t] = lp; BV[t] = v; BR[t] = r; BD[t] = d; obs = no
        with torch.no_grad(): _, _, _, _, lastv = act(net, obs)
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else BV[t + 1]; nt = 1 - BD[t]
            delta = BR[t] + gamma * nv * nt - BV[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); fm = BM.reshape(-1); fs = BS.reshape(-1); ff = BF.reshape(-1); fl = BLP.reshape(-1)
        for _ in range(epochs):
            ml, sl, fll, val = net(fo)
            dm = Categorical(logits=ml); ds = Categorical(logits=sl); dfd = Categorical(logits=fll)
            nlp = dm.log_prob(fm) + ds.log_prob(fs) + dfd.log_prob(ff); ratio = torch.exp(nlp - fl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = (dm.entropy() + ds.entropy() + dfd.entropy()).mean()
            loss = ploss + vf * vl - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 100 == 0 or it == iters - 1:
            sv, kk, K = evaluate(net, blind)
            print("  it %4d | survie %.0f%% | neutralises %.1f/%d | %.0fs" % (it, sv, kk, K, time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s.pt" % tag)
    return evaluate(net, blind)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=1200); p.add_argument("--envs", type=int, default=4096)
    a = p.parse_args()
    print("=== BRIQUE 2 : R2 tir reactif VISE + R3 micro-couvert — A/B voyant vs aveugle ===", flush=True)
    sv, kk, K = train(blind=False, iters=a.iters, envs=a.envs, tag="reflex_r23wh_voyant")
    bv, bk, _ = train(blind=True, iters=a.iters, envs=a.envs, tag="reflex_r23wh_aveugle")
    print("\n=== RESULTAT ===", flush=True)
    print("VOYANT  : survie %.0f%% | neutralises %.1f/%d" % (sv, kk, K), flush=True)
    print("AVEUGLE : survie %.0f%% | neutralises %.1f/%d" % (bv, bk, K), flush=True)
    print("ECART : survie +%.0f pts | neutralisation +%.1f tireurs" % (sv - bv, kk - bk), flush=True)
