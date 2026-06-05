"""ETAPE A v3 — KotH 3 camps, POLITIQUE PARTAGEE. UN seul reseau pilote les 3 factions (self-play a 1 cerveau).
Les 3 camps alimentent le MEME buffer (3x les donnees) -> une seule mise a jour PPO. Jeu symetrique -> trainard
impossible par construction. On verifie : equilibre ~0.33/0.33/0.33 STABLE (ecart petit, pas d'effondrement) +
qualite du jeu via le taux de parties decidees (nuls = deni mutuel = equilibre des forces). Env = toy_koth3 (obs 10)."""
import time, argparse
import numpy as np
import torch
from torch.distributions import Categorical
from toy_koth3 import ToyKoth3
from train_mem import FF
from train_selfplay import ppo_update

NAMES = ["BLU", "OPF", "IND"]


def train(iters=600, envs=512, rollout=24, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=64, hit=0.18, secn=2, seed=0, save="koth3v3"):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = ToyKoth3(num_envs=envs, hit=hit, secure_n=secn, seed=seed)
    obs = env.reset(); C = env.C; N, A, O = obs[0].shape; W = C * N
    net = FF(O, env.n_actions, A, hidden).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    T = rollout
    ot = [torch.as_tensor(obs[c], dtype=torch.float32, device=dev) for c in range(C)]
    wins = [[] for _ in range(C)]; dec = []; gstep = 0; t0 = time.time()
    print("KOTH3v3 (politique PARTAGEE) | device=%s | N=%d A=%d O=%d camps=%d largeur_buffer=%d"
          % (dev, N, A, O, C, W), flush=True)
    for it in range(iters):
        B = dict(obs=torch.zeros(T, W, A, O, device=dev), act=torch.zeros(T, W, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, W, A, device=dev), rew=torch.zeros(T, W, device=dev),
                 val=torch.zeros(T, W, device=dev), done=torch.zeros(T, W, device=dev))
        for t in range(T):
            acts = []
            with torch.no_grad():
                for c in range(C):
                    sl = slice(c * N, (c + 1) * N)
                    d = Categorical(logits=net.a_logits(ot[c])); a = d.sample()
                    B["obs"][t, sl] = ot[c]; B["act"][t, sl] = a; B["logp"][t, sl] = d.log_prob(a); B["val"][t, sl] = net.value(ot[c])
                    acts.append(a.cpu().numpy())
            nobs, rews, done, info = env.step(acts)
            dt = torch.as_tensor(done, device=dev)
            for c in range(C):
                sl = slice(c * N, (c + 1) * N)
                B["rew"][t, sl] = torch.as_tensor(rews[c], device=dev); B["done"][t, sl] = dt
            for n in np.where(done)[0]:
                if info["decided"][n]:
                    w = int(info["winner"][n])
                    for c in range(C):
                        wins[c].append(1.0 if c == w else 0.0)
                    dec.append(1.0)
                else:
                    dec.append(0.0)
            ot = [torch.as_tensor(nobs[c], dtype=torch.float32, device=dev) for c in range(C)]; gstep += N
        with torch.no_grad():
            lastv = torch.cat([net.value(ot[c]) for c in range(C)])
        ppo_update(net, opt, B["obs"], B["act"], B["logp"], B["rew"], B["val"], B["done"], lastv, cfg, dev)
        if it % 20 == 0 or it == iters - 1:
            tm = lambda x: float(np.mean(x[-3000:])) if x else 0.0
            sp = max(tm(wins[c]) for c in range(C)) - min(tm(wins[c]) for c in range(C))
            print("it %4d | %s %.2f | %s %.2f | %s %.2f | decidees %.2f | ecart %.2f | %.0f tr/s"
                  % (it, NAMES[0], tm(wins[0]), NAMES[1], tm(wins[1]), NAMES[2], tm(wins[2]), tm(dec), sp, gstep / (time.time() - t0)), flush=True)
    tm = lambda x: float(np.mean(x[-3000:])) if x else 0.0
    spread = max(tm(wins[c]) for c in range(C)) - min(tm(wins[c]) for c in range(C))
    print("[fini] %s %.2f | %s %.2f | %s %.2f | decidees %.2f | ecart(max-min) %.2f"
          % (NAMES[0], tm(wins[0]), NAMES[1], tm(wins[1]), NAMES[2], tm(wins[2]), tm(dec), spread), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/%s_shared.pt" % save)
    return [tm(wins[c]) for c in range(C)], tm(dec), spread


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=512)
    p.add_argument("--rollout", type=int, default=24); p.add_argument("--hit", type=float, default=0.18)
    p.add_argument("--secn", type=int, default=2); p.add_argument("--seed", type=int, default=0)
    p.add_argument("--save", type=str, default="koth3v3")
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, rollout=a.rollout, hit=a.hit, secn=a.secn, seed=a.seed, save=a.save)
