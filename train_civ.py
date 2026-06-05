"""train_civ — CIVILS EN DEEP LEARNING (commande Younes) : une politique neuronale PARTAGÉE par région
apprend le comportement civil face aux menaces. Obs locales (9 feat. : pop, force, menaces G/D, issues
même-camp, capitale/colline, temps) → action par région {0=rester, 1=fuir-Gauche, 2=fuir-Droite}
(quantum civ_flee : le réseau choisit QUAND et OÙ, pas combien). Reward = -morts (survie pure, v1 assumée
sans attachement productif). PPO partagé-avantage (chaque région = un échantillon, avantage de l'env).
La GUERRE reste scriptée (monde AAA) : on isole l'apprentissage CIVIL de tout le reste.
Baselines évaluées : NO-FLEE (personne ne bouge) / RÈGLE scriptée / RL. Question : le RL bat-il la règle
(anticipation des pointes massées) — et par quel comportement ?"""
import time, argparse, torch
import torch.nn as nn
from geo_gpu import GeoGPU

class CivNet(nn.Module):
    def __init__(self, fin=9, h=64):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(fin, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.pi = nn.Linear(h, 3)                      # logits {rester, G, D} par région
        self.v = nn.Linear(h, 1)                       # valeur : moyenne des embeddings régionaux → scalaire/env

    def forward(self, obs):                            # obs (N, R, F)
        z = self.tr(obs)
        return self.pi(z), self.v(z.mean(1)).squeeze(-1)


def masked_logits(logits, lok, rok):                   # interdit de fuir vers une région d'un autre camp
    logits = logits.clone()
    logits[..., 1] = logits[..., 1] + (lok - 1.0) * 1e9
    logits[..., 2] = logits[..., 2] + (rok - 1.0) * 1e9
    return logits


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--envs", type=int, default=4096); p.add_argument("--iters", type=int, default=300)
    p.add_argument("--rollout", type=int, default=32); p.add_argument("--doctrines", type=str, default="AAA")
    p.add_argument("--lr", type=float, default=3e-4); p.add_argument("--save", type=str, default="civ_learner.pt")
    a = p.parse_args()
    dev = "cuda:0"; torch.manual_seed(0)

    net = CivNet().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=a.lr)
    env = GeoGPU(num_envs=a.envs, n_countries=3, arc=4, hold_T=5, doctrines=a.doctrines, device=dev, seed=0)
    R = env.R; N = a.envs; T = a.rollout
    GAMMA, LAM, CLIP, EPOCHS, MB = 0.97, 0.95, 0.2, 4, 8192   # MB en échantillons (env-pas)


    def evaluate(policy_kind, steps=200, seed=1):
        """morts/pop0 moyens sur guerres finies. policy_kind: none|scripted|rl"""
        e = GeoGPU(num_envs=2048, n_countries=3, arc=4, hold_T=5, doctrines=a.doctrines, device=dev, seed=seed)
        if policy_kind == "none":
            pol = lambda o, l, r: torch.zeros(o.shape[0], o.shape[1], dtype=torch.long, device=dev)
        elif policy_kind == "rl":
            def pol(o, l, r):
                with torch.no_grad():
                    lg, _ = net(o)
                return masked_logits(lg, l, r).argmax(-1)
        else:
            pol = None
        dead = 0.0; nwars = 0
        for _ in range(steps):
            done, info = e.step(auto_reset=False, civ_policy=pol)
            dm = done.bool()
            if dm.any():
                idx = dm.nonzero(as_tuple=True)[0]
                dead += (info["civ_dead"][idx] / e.pop0_total).sum().item(); nwars += idx.numel()
            e._reset(dm.nonzero(as_tuple=True)[0])
        return dead / max(nwars, 1), nwars


    print("CIV-RL | envs=%d rollout=%d iters=%d | monde %s | reward=-morts" % (N, T, a.iters, a.doctrines), flush=True)
    b_none, _ = evaluate("none"); b_scr, _ = evaluate("scripted")
    print("BASELINES morts/pop0 : no-flee %.3f | règle scriptée %.3f" % (b_none, b_scr), flush=True)

    prev_dead = torch.zeros(N, device=dev)
    t0 = time.time()
    for it in range(a.iters):
        OBS = torch.zeros(T, N, R, 9, device=dev); ACT = torch.zeros(T, N, R, dtype=torch.long, device=dev)
        LP = torch.zeros(T, N, R, device=dev); VAL = torch.zeros(T, N, device=dev)
        REW = torch.zeros(T, N, device=dev); DONE = torch.zeros(T, N, device=dev)
        LOK = torch.zeros(T, N, R, device=dev); ROK = torch.zeros(T, N, R, device=dev)
        for t in range(T):
            slot = {}
            def pol(o, l, r, _t=t, _s=slot):
                with torch.no_grad():
                    lg, v = net(o)
                lg = masked_logits(lg, l, r)
                dist = torch.distributions.Categorical(logits=lg)
                act = dist.sample()
                OBS[_t] = o; ACT[_t] = act; LP[_t] = dist.log_prob(act); VAL[_t] = v
                LOK[_t] = l; ROK[_t] = r
                return act
            done, info = env.step(auto_reset=True, civ_policy=pol)
            REW[t] = -(info["civ_dead"] - prev_dead) / env.pop0_total * 10.0
            DONE[t] = done.float()
            prev_dead = info["civ_dead"].clone(); prev_dead[done] = 0.0
        with torch.no_grad():
            _, last_v = net(env.civ_obs()[0])
        adv = torch.zeros(T, N, device=dev); gae = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nxt = last_v if t == T - 1 else VAL[t + 1]
            nd = 1.0 - DONE[t]
            delta = REW[t] + GAMMA * nxt * nd - VAL[t]
            gae = delta + GAMMA * LAM * nd * gae
            adv[t] = gae
        ret = adv + VAL
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        obs_f = OBS.reshape(T * N, R, 9); act_f = ACT.reshape(T * N, R); lp_f = LP.reshape(T * N, R)
        lok_f = LOK.reshape(T * N, R); rok_f = ROK.reshape(T * N, R)
        adv_f = adv.reshape(T * N); ret_f = ret.reshape(T * N)
        for _ in range(EPOCHS):
            perm = torch.randperm(T * N, device=dev)
            for k in range(0, T * N, MB):
                mb = perm[k:k + MB]
                lg, v = net(obs_f[mb])
                lg = masked_logits(lg, lok_f[mb], rok_f[mb])
                dist = torch.distributions.Categorical(logits=lg)
                lp = dist.log_prob(act_f[mb])                              # (mb, R)
                ratio = (lp - lp_f[mb]).exp()
                A = adv_f[mb][:, None]                                     # avantage d'env partagé par région
                l_pi = -torch.min(ratio * A, ratio.clamp(1 - CLIP, 1 + CLIP) * A).mean()
                l_v = 0.5 * (v - ret_f[mb]).pow(2).mean()
                l_e = -0.01 * dist.entropy().mean()
                opt.zero_grad(); (l_pi + l_v + l_e).backward()
                nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 20 == 0 or it == a.iters - 1:
            rl, nw = evaluate("rl")
            flee_rate = (ACT > 0).float().mean().item()
            print("it %3d | morts RL %.3f (no-flee %.3f, règle %.3f) | %%fuite %.2f | rew/pas %.4f | %.0fs"
                  % (it, rl, b_none, b_scr, flee_rate, REW.mean().item(), time.time() - t0), flush=True)
    torch.save(net.state_dict(), a.save)
    rl, nw = evaluate("rl", steps=400, seed=2)
    print("[FINAL seed2] morts RL %.3f vs no-flee %.3f vs règle %.3f | guerres éval %d | modèle → %s"
          % (rl, b_none, b_scr, nw, a.save), flush=True)
