"""train_leviathan.py — ETAGE 1 : PPO sur LeviathanEnv. Un pays apprend SEUL a prosperer (tenir sa logistique).
Curriculum menace 0.30 -> 0.45. On compare la politique APPRISE au BASELINE reactif DANS LE MEME ENV (apples-to-apples)."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from leviathan_env import LeviathanEnv
from leviathan_env2 import LeviathanEnv2
from leviathan_econ import LeviathanEcon

DEV = "cuda:0"


class Net(nn.Module):
    def __init__(self, obs, K, h=256):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.pi = nn.Linear(h, K * 3); self.v = nn.Linear(h, 1); self.K = K

    def forward(self, o):
        z = self.b(o); return self.pi(z).view(-1, self.K, 3), self.v(z).squeeze(-1)


def act(net, o, greedy=False):
    lg, v = net(o); d = Categorical(logits=lg)
    a = lg.argmax(-1) if greedy else d.sample()
    return a, d.log_prob(a).sum(-1), v, d


def heuristic_act(env):
    # BASELINE reactif : RENFORCER le secteur tenu le plus faible, sinon TENIR (+ recrutement si l'env le gere)
    if hasattr(env, "baseline_action"):
        return env.baseline_action()
    a = torch.zeros(env.N, env.K, dtype=torch.long, device=env.dev)
    g = env.garr.clone(); g[env.owner <= 0] = 1e9
    a[torch.arange(env.N, device=env.dev), g.argmin(1)] = 1
    return a


@torch.no_grad()
def evaluate(env, net, threat, rounds=6):
    env.threat_rate = threat; o = env.reset(); survived = []
    for _ in range(env.max_steps * rounds):
        a = heuristic_act(env) if net is None else act(net, o, greedy=True)[0]
        o, r, done, info = env.step(a)
        di = torch.where(done > 0)[0]
        if di.numel() > 0:
            survived.append(info["survived"][di].float())
    return torch.cat(survived).mean().item() if survived else 0.0


def train(iters=600, envs=4096, T=16, lr=3e-4, h=256, seed=0, tag="leviathan", threat=0.37, env_cls=LeviathanEnv):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.01
    lo = 0.20   # bas du curriculum
    env = env_cls(num_envs=envs, device=DEV, seed=seed, threat_rate=lo)
    ev = env_cls(num_envs=2048, device=DEV, seed=12345)
    net = Net(env.obs_dim, env.n_heads, h).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    o = env.reset(); O = env.obs_dim; t0 = time.time()
    base = evaluate(ev, None, threat)
    print("LEVIATHAN etage1 | dev=%s N=%d K=%d O=%d | menace cible=%.2f | BASELINE survie=%.2f\n" % (DEV, envs, env.K, O, threat, base), flush=True)
    for it in range(iters):
        env.threat_rate = min(threat, lo + (threat - lo) * it / max(1, iters * 0.6))   # curriculum
        ob = torch.zeros(T, envs, O, device=DEV); ac = torch.zeros(T, envs, env.n_heads, dtype=torch.long, device=DEV)
        lp = torch.zeros(T, envs, device=DEV); vl = torch.zeros(T, envs, device=DEV)
        rw = torch.zeros(T, envs, device=DEV); dn = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            with torch.no_grad():
                a, l, v, _ = act(net, o)
            no, r, done, info = env.step(a)
            ob[t] = o; ac[t] = a; lp[t] = l; vl[t] = v; rw[t] = r; dn[t] = done; o = no
        with torch.no_grad():
            _, lastv = net(o)
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else vl[t + 1]; nt = 1 - dn[t]
            delta = rw[t] + gamma * nv * nt - vl[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + vl).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = ob.reshape(-1, O); fa = ac.reshape(-1, env.n_heads); fl = lp.reshape(-1)
        for _ in range(epochs):
            lg, val = net(fo); dist = Categorical(logits=lg); nlp = dist.log_prob(fa).sum(-1)
            ratio = torch.exp(nlp - fl)
            pl = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vloss = ((val - ret) ** 2).mean(); en = dist.entropy().sum(-1).mean()
            loss = pl + vf * vloss - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 50 == 0 or it == iters - 1:
            sr = evaluate(ev, net, threat)
            print("it %4d | menace_train %.2f | APPRIS survie@%.2f %.2f (baseline %.2f) | %.0fs"
                  % (it, env.threat_rate, threat, sr, base, time.time() - t0), flush=True)
    learned = evaluate(ev, net, threat)
    print("\n[fini] survie@menace%.2f : BASELINE %.2f  ->  APPRIS %.2f  (gain %+.2f)" % (threat, base, learned, learned - base), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s_policy.pt" % tag)
    print("[fini] politique -> leviathan/%s_policy.pt" % tag, flush=True)
    return base, learned


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=4096)
    p.add_argument("--tag", type=str, default="leviathan"); p.add_argument("--threat", type=float, default=0.37)
    p.add_argument("--env2", action="store_true", help="etage 2 : ennemi concentre (LeviathanEnv2)")
    p.add_argument("--econ", action="store_true", help="substrat v3 : economie + recrutement (LeviathanEcon)")
    a = p.parse_args()
    ENVC = LeviathanEcon if a.econ else (LeviathanEnv2 if a.env2 else LeviathanEnv)
    train(iters=a.iters, envs=a.envs, tag=a.tag, threat=a.threat, env_cls=ENVC)
