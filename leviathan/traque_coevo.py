"""traque_coevo.py — ETAPE B : CO-EVOLUTION traquer <-> se cacher.
Les 40 FS (politique partagee, warm-start traque_fs.pt) ET le PAYS (politique de commandement : OU concentrer
la traque = quel noeud surveiller) apprennent EN MEME TEMPS, l'un contre l'autre. Le pays doit apprendre a
ANTICIPER (proteger ses radars, deviner ou frappent les FS) ; les FS a contrer le pays qui se durcit.
On suit la coercition : elle doit BAISSER a mesure que le pays apprend a traquer (puis les FS re-adaptent)."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from traque_env import TraqueEnv
from traque_train import FSNet, act as act_fs

DEV = "cuda:0"


class CountryNet(nn.Module):
    def __init__(self, obs, Z, K, h=160):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.f = nn.Linear(h, Z * K); self.v = nn.Linear(h, 1); self.Z = Z; self.K = K

    def forward(self, o):
        z = self.b(o); return self.f(z).view(-1, self.K, self.Z), self.v(z).squeeze(-1)


def act_country(net, oc, greedy=False):
    lg, v = net(oc); d = Categorical(logits=lg)        # lg (N,K,Z) : K equipes sur Z zones
    a = lg.argmax(-1) if greedy else d.sample()        # (N,K)
    return a, d.log_prob(a).sum(-1), v


def gae(R, V, D, lastv, gamma, lam, per_agent=False):
    T = R.shape[0]; adv = torch.zeros_like(R); g = torch.zeros_like(R[0])
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else V[t + 1]
        nt = (1 - D[t])[:, None] if per_agent else (1 - D[t])
        delta = R[t] + gamma * nv * nt - V[t]; g = delta + gamma * lam * nt * g; adv[t] = g
    return adv


def train(iters=400, envs=512, T=16, lr=3e-4, h=160, hc=128, seed=0, tag="traque_coevo", warm="traque_fs.pt"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.02
    env = TraqueEnv(num_envs=envs, device=DEV, seed=seed)
    F = env.n_fs; O = env.obs_dim; M = env.M; OC = env.country_obs_dim
    fs = FSNet(O, M, h).to(DEV)
    try:
        fs.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/%s" % warm)); print("[warm] FS <- %s" % warm, flush=True)
    except Exception as e:
        print("[warm] pas de warm-start (%s)" % e, flush=True)
    Z = env.Z; K = env.n_teams; co = CountryNet(OC, Z, K, hc).to(DEV)
    fopt = torch.optim.Adam(fs.parameters(), lr=lr); copt = torch.optim.Adam(co.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("CO-EVO TRAQUE | N=%d FS=%d O=%d OC=%d noeuds=%d" % (envs, F, O, OC, M), flush=True)
    for it in range(iters):
        # buffers FS (par agent) + PAYS (single)
        BO = torch.zeros(T, envs, F, O, device=DEV); BTG = torch.zeros(T, envs, F, dtype=torch.long, device=DEV)
        BPO = torch.zeros(T, envs, F, dtype=torch.long, device=DEV); BLP = torch.zeros(T, envs, F, device=DEV)
        BV = torch.zeros(T, envs, F, device=DEV); BR = torch.zeros(T, envs, F, device=DEV); BM = torch.zeros(T, envs, M, device=DEV)
        CO = torch.zeros(T, envs, OC, device=DEV); CA = torch.zeros(T, envs, K, dtype=torch.long, device=DEV)
        CLP = torch.zeros(T, envs, device=DEV); CV = torch.zeros(T, envs, device=DEV); CR = torch.zeros(T, envs, device=DEV)
        BD = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            na = env.node_alive.clone(); oc = env.obs_country()
            with torch.no_grad():
                tg, po, lp, v = act_fs(fs, obs, na)
                ca, clp, cv = act_country(co, oc)
            no, r, done, info = env.step(tg, po, ca)
            BO[t] = obs; BTG[t] = tg; BPO[t] = po; BLP[t] = lp; BV[t] = v; BR[t] = r; BM[t] = na; BD[t] = done
            CO[t] = oc; CA[t] = ca; CLP[t] = clp; CV[t] = cv; CR[t] = info["rew_country"]
            obs = no
        with torch.no_grad():
            _, _, _, flv = act_fs(fs, obs, env.node_alive); _, _, clv = act_country(co, env.obs_country())
        # --- update FS (par agent) ---
        adv = gae(BR, BV, BD, flv, gamma, lam, per_agent=True)
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); ftg = BTG.reshape(-1); fpo = BPO.reshape(-1); fl = BLP.reshape(-1)
        fm = BM[:, :, None, :].expand(T, envs, F, M).reshape(-1, M)
        for _ in range(epochs):
            tl, pl, val = fs(fo); tl = tl.masked_fill(fm <= 0, -1e9)
            dt = Categorical(logits=tl); dp = Categorical(logits=pl)
            nlp = dt.log_prob(ftg) + dp.log_prob(fpo); ratio = torch.exp(nlp - fl)
            pls = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            loss = pls + vf * ((val - ret) ** 2).mean() - ent * (dt.entropy() + dp.entropy()).mean()
            fopt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(fs.parameters(), 0.5); fopt.step()
        # --- update PAYS (single) ---
        cadv = gae(CR, CV, BD, clv, gamma, lam, per_agent=False)
        cret = (cadv + CV).reshape(-1); cadvn = ((cadv - cadv.mean()) / (cadv.std() + 1e-8)).reshape(-1)
        co_o = CO.reshape(-1, OC); co_a = CA.reshape(-1, K); co_l = CLP.reshape(-1)
        for _ in range(epochs):
            lg, val = co(co_o); d = Categorical(logits=lg); nlp = d.log_prob(co_a).sum(-1); ratio = torch.exp(nlp - co_l)
            pls = -torch.min(ratio * cadvn, torch.clamp(ratio, 1 - clip, 1 + clip) * cadvn).mean()
            loss = pls + vf * ((val - cret) ** 2).mean() - ent * d.entropy().sum(-1).mean()
            copt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(co.parameters(), 0.5); copt.step()
        if it % 40 == 0 or it == iters - 1:
            c, a, s = evaluate(fs, co)
            print("it %4d | coercion FS %.1f/88 | FS survivants %.1f/40 | capteurs restants %.1f/5 | %.0fs"
                  % (it, c, a, s, time.time() - t0), flush=True)
    torch.save(fs.state_dict(), "/home/younes/arma3-marl/leviathan/%s_fs.pt" % tag)
    torch.save(co.state_dict(), "/home/younes/arma3-marl/leviathan/%s_pays.pt" % tag)
    print("[fini] -> %s_fs.pt / %s_pays.pt" % (tag, tag), flush=True)


@torch.no_grad()
def evaluate(fs, co, n=1024, seed=555, n_fs=40, fs_evade=1.0):
    import statistics as st
    e = TraqueEnv(num_envs=n, device=DEV, seed=seed, n_fs=n_fs, fs_evade=fs_evade); obs = e._obs(); C, A, S = [], [], []
    for _ in range(e.max_steps * 2):
        tg, po, _, _ = act_fs(fs, obs, e.node_alive, greedy=True)
        ca, _, _ = act_country(co, e.obs_country(), greedy=True)
        obs, r, d, info = e.step(tg, po, ca)
        for i in torch.where(d > 0)[0].tolist():
            C.append(info["coercion"][i].item()); A.append(info["fs_alive"][i].item()); S.append(info["sensors_left"][i].item())
    return (st.mean(C) if C else 0), (st.mean(A) if A else 0), (st.mean(S) if S else 0)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=400); p.add_argument("--envs", type=int, default=512); p.add_argument("--tag", type=str, default="traque_coevo")
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, tag=a.tag)
