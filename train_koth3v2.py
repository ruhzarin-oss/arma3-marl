"""ETAPE A v2 — KotH 3 camps avec COALITION INCITEE (signal de leader + recompense de delogement).
Init IDENTIQUE des 3 reseaux (--same_init) pour separer la chance d'init de la dynamique.
On veut voir : le leader est-il activement concentre -> retour vers ~0.33 chacun + ecart(max-min) plus petit qu'en v1 (0.45)."""
import time, argparse
import numpy as np
import torch
from torch.distributions import Categorical
from toy_koth3v2 import ToyKoth3V2
from train_mem import FF
from train_selfplay import ppo_update

NAMES = ["BLU", "OPF", "IND"]


def train(iters=600, envs=512, rollout=24, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=64, hit=0.18, secn=2, focus=1.5,
          same_init=True, seed=0, save="koth3v2"):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = ToyKoth3V2(num_envs=envs, hit=hit, secure_n=secn, focus=focus, seed=seed)
    obs = env.reset(); C = env.C; N, A, O = obs[0].shape
    nets = [FF(O, env.n_actions, A, hidden).to(dev) for _ in range(C)]
    if same_init:
        sd = nets[0].state_dict()
        for c in range(1, C):
            nets[c].load_state_dict({k: v.clone() for k, v in sd.items()})
    opts = [torch.optim.Adam(nets[c].parameters(), lr=lr) for c in range(C)]
    T = rollout
    ot = [torch.as_tensor(obs[c], dtype=torch.float32, device=dev) for c in range(C)]
    wins = [[] for _ in range(C)]; dec = []; gstep = 0; t0 = time.time()
    print("KOTH3v2 | device=%s | N=%d A=%d O=%d camps=%d focus=%.2f same_init=%s"
          % (dev, N, A, O, C, focus, same_init), flush=True)
    for it in range(iters):
        B = [dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                  logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                  val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev)) for _ in range(C)]
        for t in range(T):
            acts = []
            with torch.no_grad():
                for c in range(C):
                    d = Categorical(logits=nets[c].a_logits(ot[c])); a = d.sample()
                    B[c]["obs"][t] = ot[c]; B[c]["act"][t] = a; B[c]["logp"][t] = d.log_prob(a); B[c]["val"][t] = nets[c].value(ot[c])
                    acts.append(a.cpu().numpy())
            nobs, rews, done, info = env.step(acts)
            for c in range(C):
                B[c]["rew"][t] = torch.as_tensor(rews[c], device=dev); B[c]["done"][t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]:
                if info["decided"][n]:
                    w = int(info["winner"][n])
                    for c in range(C):
                        wins[c].append(1.0 if c == w else 0.0)
                    dec.append(1.0)
                else:
                    dec.append(0.0)
            ot = [torch.as_tensor(nobs[c], dtype=torch.float32, device=dev) for c in range(C)]; gstep += N
        for c in range(C):
            with torch.no_grad():
                lv = nets[c].value(ot[c])
            ppo_update(nets[c], opts[c], B[c]["obs"], B[c]["act"], B[c]["logp"], B[c]["rew"], B[c]["val"], B[c]["done"], lv, cfg, dev)
        if it % 20 == 0 or it == iters - 1:
            tm = lambda x: float(np.mean(x[-3000:])) if x else 0.0
            sp = max(tm(wins[c]) for c in range(C)) - min(tm(wins[c]) for c in range(C))
            print("it %4d | %s %.2f | %s %.2f | %s %.2f | decidees %.2f | ecart %.2f | %.0f tr/s"
                  % (it, NAMES[0], tm(wins[0]), NAMES[1], tm(wins[1]), NAMES[2], tm(wins[2]), tm(dec), sp, gstep / (time.time() - t0)), flush=True)
    tm = lambda x: float(np.mean(x[-3000:])) if x else 0.0
    spread = max(tm(wins[c]) for c in range(C)) - min(tm(wins[c]) for c in range(C))
    print("[fini] %s %.2f | %s %.2f | %s %.2f | decidees %.2f | ecart(max-min) %.2f"
          % (NAMES[0], tm(wins[0]), NAMES[1], tm(wins[1]), NAMES[2], tm(wins[2]), tm(dec), spread), flush=True)
    for c in range(C):
        torch.save(nets[c].state_dict(), "/home/younes/arma3-marl/%s_%s.pt" % (save, NAMES[c].lower()))
    return [tm(wins[c]) for c in range(C)], tm(dec), spread


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=512)
    p.add_argument("--rollout", type=int, default=24); p.add_argument("--hit", type=float, default=0.18)
    p.add_argument("--secn", type=int, default=2); p.add_argument("--focus", type=float, default=1.5)
    p.add_argument("--seed", type=int, default=0); p.add_argument("--no_same_init", action="store_true")
    p.add_argument("--save", type=str, default="koth3v2")
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, rollout=a.rollout, hit=a.hit, secn=a.secn, focus=a.focus,
          same_init=not a.no_same_init, seed=a.seed, save=a.save)
