"""traque_train.py — ETAPE A : les 40 FS APPRENNENT (MARL) a evader + coercer contre le pays SCRIPTE.
Politique PARTAGEE par FS : encode (soi + tous les noeuds + global) -> tete CIBLE (lequel des 22 noeuds viser,
masquee sur les noeuds vivants) + tete POSTURE (vite/prudent/cache). MAPPO (recompense d'equipe = coercition).
Etape B (apres) : le pays apprend aussi (surge/recherche) -> co-evolution traquer<->se cacher."""
import time, argparse, statistics as st
import torch, torch.nn as nn
from torch.distributions import Categorical
from traque_env import TraqueEnv

DEV = "cuda:0"


class FSNet(nn.Module):
    def __init__(self, obs, M, h=160):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.tgt = nn.Linear(h, M); self.post = nn.Linear(h, 5); self.v = nn.Linear(h, 1); self.M = M   # 5 postures (3=leurre 4=fumigene)

    def forward(self, o):
        z = self.b(o); return self.tgt(z), self.post(z), self.v(z).squeeze(-1)


def act(net, obs, node_alive, greedy=False):
    N, F, O = obs.shape
    tl, pl, v = net(obs.reshape(-1, O))
    tl = tl.view(N, F, -1); pl = pl.view(N, F, -1); v = v.view(N, F)
    tl = tl.masked_fill(node_alive[:, None, :].expand(N, F, net.M) <= 0, -1e9)   # pas de cible morte
    dt = Categorical(logits=tl); dp = Categorical(logits=pl)
    tg = tl.argmax(-1) if greedy else dt.sample(); po = pl.argmax(-1) if greedy else dp.sample()
    return tg, po, dt.log_prob(tg) + dp.log_prob(po), v


@torch.no_grad()
def evaluate(net, n=1024, seed=777):
    e = TraqueEnv(num_envs=n, device=DEV, seed=seed); obs = e._obs(); co, al, se = [], [], []
    for _ in range(e.max_steps * 2):
        tg, po, _, _ = act(net, obs, e.node_alive, greedy=True)
        obs, r, d, info = e.step(tg, po)
        for i in torch.where(d > 0)[0].tolist():
            co.append(info["coercion"][i].item()); al.append(info["fs_alive"][i].item()); se.append(info["sensors_left"][i].item())
    return (st.mean(co) if co else 0), (st.mean(al) if al else 0), (st.mean(se) if se else 0)


def train(iters=400, envs=512, T=16, lr=3e-4, h=160, seed=0, tag="traque_fs"):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.02
    env = TraqueEnv(num_envs=envs, device=DEV, seed=seed)
    F = env.n_fs; O = env.obs_dim; M = env.M
    net = FSNet(O, M, h).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("TRAQUE FS | dev=%s N=%d FS=%d O=%d noeuds=%d" % (DEV, envs, F, O, M), flush=True)
    for it in range(iters):
        BO = torch.zeros(T, envs, F, O, device=DEV); BTG = torch.zeros(T, envs, F, dtype=torch.long, device=DEV)
        BPO = torch.zeros(T, envs, F, dtype=torch.long, device=DEV); BLP = torch.zeros(T, envs, F, device=DEV)
        BV = torch.zeros(T, envs, F, device=DEV); BR = torch.zeros(T, envs, F, device=DEV)
        BD = torch.zeros(T, envs, device=DEV); BM = torch.zeros(T, envs, M, device=DEV)
        for t in range(T):
            na = env.node_alive.clone()
            with torch.no_grad():
                tg, po, lp, v = act(net, obs, na)
            no, r, done, info = env.step(tg, po)
            BO[t] = obs; BTG[t] = tg; BPO[t] = po; BLP[t] = lp; BV[t] = v; BR[t] = r; BD[t] = done; BM[t] = na
            obs = no
        with torch.no_grad():
            _, _, _, lastv = act(net, obs, env.node_alive)
        adv = torch.zeros(T, envs, F, device=DEV); g = torch.zeros(envs, F, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else BV[t + 1]; nt = (1 - BD[t])[:, None]
            delta = BR[t] + gamma * nv * nt - BV[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); ftg = BTG.reshape(-1); fpo = BPO.reshape(-1); fl = BLP.reshape(-1)
        fm = BM[:, :, None, :].expand(T, envs, F, M).reshape(-1, M)
        for _ in range(epochs):
            tl, pl, val = net(fo); tl = tl.masked_fill(fm <= 0, -1e9)
            dt = Categorical(logits=tl); dp = Categorical(logits=pl)
            nlp = dt.log_prob(ftg) + dp.log_prob(fpo); ratio = torch.exp(nlp - fl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = (dt.entropy() + dp.entropy()).mean()
            loss = ploss + vf * vl - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 40 == 0 or it == iters - 1:
            co, al, se = evaluate(net)
            print("it %4d | coercion %.1f/88 | FS survivants %.1f/40 | capteurs restants %.1f/5 | %.0fs"
                  % (it, co, al, se, time.time() - t0), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s.pt" % tag)
    print("[fini] -> %s.pt" % tag, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=400); p.add_argument("--envs", type=int, default=512)
    p.add_argument("--tag", type=str, default="traque_fs")
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, tag=a.tag)
