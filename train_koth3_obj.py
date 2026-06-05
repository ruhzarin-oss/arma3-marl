"""ETAPE A (recadree) — KotH 3 camps, UN CERVEAU PAR CAMP, but = GAGNER/TENIR L'OBJECTIF.
Recompense DOMINEE par le CONTROLE de la colline (kappa eleve) -> tenir l'objectif paye en continu, donc fight POUR la colline
(au lieu du 'standoff' ou personne ne bouge). + pen. de nul. Metriques : OCCUPATION (vont-ils sur la colline ?),
SECURISE (prennent-ils proprement ?), part de controle par camp. Le cycling est OK : on veut la COMPETENCE a l'objectif."""
import time, argparse
import numpy as np
import torch
from torch.distributions import Categorical
from toy_koth3 import ToyKoth3
from train_mem import FF
from train_selfplay import ppo_update

NAMES = ["BLU", "OPF", "IND"]


def train(iters=600, envs=512, rollout=24, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=64, hit=0.12, secn=2, tie_pen=0.2, kappa=0.25, seed=0, save="koth3obj"):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = ToyKoth3(num_envs=envs, hit=hit, secure_n=secn, tie_pen=tie_pen, kappa=kappa, seed=seed)
    obs = env.reset(); C = env.C; N, A, O = obs[0].shape
    nets = [FF(O, env.n_actions, A, hidden).to(dev) for _ in range(C)]
    opts = [torch.optim.Adam(nets[c].parameters(), lr=lr) for c in range(C)]
    T = rollout
    ot = [torch.as_tensor(obs[c], dtype=torch.float32, device=dev) for c in range(C)]
    sec_all = []; sec_by = [[] for _ in range(C)]; dec = []; occ = []; gstep = 0; t0 = time.time()
    print("KOTH3-OBJ | dev=%s N=%d A=%d O=%d camps=%d | hit=%.2f tie_pen=%.2f kappa=%.2f"
          % (dev, N, A, O, C, hit, tie_pen, kappa), flush=True)
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
            occ.append(float(info["occ"].mean()))
            for c in range(C):
                B[c]["rew"][t] = torch.as_tensor(rews[c], device=dev); B[c]["done"][t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]:
                s = bool(info["secured"][n]); sec_all.append(1.0 if s else 0.0); w = int(info["winner"][n])
                for c in range(C):
                    sec_by[c].append(1.0 if (s and c == w) else 0.0)
                dec.append(1.0 if info["decided"][n] else 0.0)
            ot = [torch.as_tensor(nobs[c], dtype=torch.float32, device=dev) for c in range(C)]; gstep += N
        for c in range(C):
            with torch.no_grad():
                lv = nets[c].value(ot[c])
            ppo_update(nets[c], opts[c], B[c]["obs"], B[c]["act"], B[c]["logp"], B[c]["rew"], B[c]["val"], B[c]["done"], lv, cfg, dev)
        if it % 20 == 0 or it == iters - 1:
            tm = lambda x: float(np.mean(x[-3000:])) if x else 0.0
            to = lambda x: float(np.mean(x[-20000:])) if x else 0.0
            print("it %4d | OCCUP %.2f | SECURISE %.2f | %s=%.2f %s=%.2f %s=%.2f | decidees %.2f | %.0f tr/s"
                  % (it, to(occ), tm(sec_all), NAMES[0], tm(sec_by[0]), NAMES[1], tm(sec_by[1]), NAMES[2], tm(sec_by[2]),
                     tm(dec), gstep / (time.time() - t0)), flush=True)
    tm = lambda x: float(np.mean(x[-3000:])) if x else 0.0; to = lambda x: float(np.mean(x[-20000:])) if x else 0.0
    print("[fini] OCCUP %.2f | SECURISE %.2f | %s %.2f | %s %.2f | %s %.2f | decidees %.2f"
          % (to(occ), tm(sec_all), NAMES[0], tm(sec_by[0]), NAMES[1], tm(sec_by[1]), NAMES[2], tm(sec_by[2]), tm(dec)), flush=True)
    for c in range(C):
        torch.save(nets[c].state_dict(), "/home/younes/arma3-marl/%s_%s.pt" % (save, NAMES[c].lower()))
    return to(occ), tm(sec_all)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=600); p.add_argument("--envs", type=int, default=512)
    p.add_argument("--rollout", type=int, default=24); p.add_argument("--hit", type=float, default=0.12)
    p.add_argument("--secn", type=int, default=2); p.add_argument("--tie_pen", type=float, default=0.2)
    p.add_argument("--kappa", type=float, default=0.25); p.add_argument("--seed", type=int, default=0)
    p.add_argument("--save", type=str, default="koth3obj")
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, rollout=a.rollout, hit=a.hit, secn=a.secn, tie_pen=a.tie_pen, kappa=a.kappa, seed=a.seed, save=a.save)
