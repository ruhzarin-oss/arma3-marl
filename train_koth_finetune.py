"""ÉTAPE C.3 — FINE-TUNE dans Arma. MultiKoth (M serveurs x ArmaEnvKoth, 3 factions, threads) + un cerveau PARTAGÉ
initialisé depuis league_learner.pt, affiné par PPO dans le VRAI jeu pour fermer l'écart sim->réel (tempo).
Les 3 factions alimentent le même buffer (3x données). On suit : taux de CAPTURE et contrôle qui MONTENT."""
import time, argparse, threading
import numpy as np
import torch
from torch.distributions import Categorical
from train_koth_gpu import Net
from train_arma_selfplay import ppo

SB = "/mnt/data/harmattan-sandbox"


class MultiKoth:
    def __init__(self, num_servers=12, per_server=3, **kw):
        from arma_env_koth import ArmaEnvKoth
        self.envs = [ArmaEnvKoth(num_envs=per_server,
                                 mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % i,
                                 log=SB + "/logs/server%d.out" % i, seed=i, **kw) for i in range(num_servers)]
        self.C = 3; self.n_actions = self.envs[0].n_actions; self.obs_dim = self.envs[0].obs_dim; self.A = self.envs[0].A
        self.sizes = [e.N for e in self.envs]; self.N = sum(self.sizes); self._sp = np.cumsum(self.sizes)[:-1]

    def _par(self, fns):
        res = [None] * len(self.envs); th = []
        for i in range(len(self.envs)):
            t = threading.Thread(target=lambda i=i: res.__setitem__(i, fns[i]())); t.start(); th.append(t)
        for t in th: t.join()
        return res

    def reset(self):
        r = self._par([(lambda e=e: e.reset()) for e in self.envs])
        return tuple(np.concatenate([x[c] for x in r], 0) for c in range(self.C))

    def step(self, acts):
        parts = [np.split(acts[c], self._sp, 0) for c in range(self.C)]
        r = self._par([(lambda e=self.envs[i], a=[parts[c][i] for c in range(self.C)]: e.step(a[0], a[1], a[2])) for i in range(len(self.envs))])
        obs = tuple(np.concatenate([x[0][c] for x in r], 0) for c in range(self.C))
        rew = tuple(np.concatenate([x[1][c] for x in r], 0) for c in range(self.C))
        done = np.concatenate([x[2] for x in r], 0)
        info = {k: np.concatenate([x[3][k] for x in r], 0) for k in ("winner", "decided", "captured")}
        return obs, rew, done, info


def train(iters=40, servers=12, per_server=3, rollout=12, lr=1e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=512, layers=3, move=36, init="league_learner.pt", save="koth_finetuned"):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = MultiKoth(num_servers=servers, per_server=per_server, move=move)
    C, A, O, NA = env.C, env.A, env.obs_dim, env.n_actions; N = env.N; W = C * N; T = rollout
    net = Net(O, NA, hidden, layers).to(dev)
    try:
        net.load_state_dict(torch.load("/home/younes/arma3-marl/" + init, map_location=dev)); print("WARM-START " + init, flush=True)
    except Exception as e:
        print("init aleatoire (", e, ")", flush=True)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env.reset(); ot = list(obs)
    caps = []; decs = []; t0 = time.time(); gstep = 0
    print("C.3 FINE-TUNE | env pret: N=%d (x%d camps) A=%d O=%d | move=%d" % (N, C, A, O, move), flush=True)
    for it in range(iters):
        B = dict(obs=torch.zeros(T, W, A, O, device=dev), act=torch.zeros(T, W, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, W, A, device=dev), rew=torch.zeros(T, W, device=dev),
                 val=torch.zeros(T, W, device=dev), done=torch.zeros(T, W, device=dev))
        capc = 0; decc = 0; donec = 0
        for t in range(T):
            acts = []
            with torch.no_grad():
                for c in range(C):
                    sl = slice(c * N, (c + 1) * N); tt = torch.as_tensor(ot[c], dtype=torch.float32, device=dev)
                    d = Categorical(logits=net.a_logits(tt)); a = d.sample()
                    B["obs"][t, sl] = tt; B["act"][t, sl] = a; B["logp"][t, sl] = d.log_prob(a); B["val"][t, sl] = net.value(tt)
                    acts.append(a.cpu().numpy())
            nobs, rews, done, info = env.step(acts)
            for c in range(C):
                sl = slice(c * N, (c + 1) * N)
                B["rew"][t, sl] = torch.as_tensor(rews[c], device=dev); B["done"][t, sl] = torch.as_tensor(done, device=dev)
            capc += int(info["captured"].sum()); decc += int(info["decided"].sum()); donec += int(done.sum())
            ot = list(nobs); gstep += N
        with torch.no_grad():
            lastv = torch.cat([net.value(torch.as_tensor(ot[c], dtype=torch.float32, device=dev)) for c in range(C)])
        ppo(net, opt, B, lastv, cfg, dev)
        caps.append(capc); decs.append(decc)
        print("it %3d | captures %3d | decidees %3d | fins %3d | %.1f tr/s | %s" %
              (it, capc, decc, donec, gstep / (time.time() - t0), time.strftime("%H:%M:%S")), flush=True)
        torch.save(net.state_dict(), "/home/younes/arma3-marl/%s.pt" % save)
    print("[fini] captures totales %d sur %d its | cerveau -> %s.pt" % (sum(caps), iters, save), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=40); p.add_argument("--servers", type=int, default=12)
    p.add_argument("--per_server", type=int, default=3); p.add_argument("--rollout", type=int, default=12)
    p.add_argument("--move", type=int, default=36); p.add_argument("--init", type=str, default="league_learner.pt")
    p.add_argument("--save", type=str, default="koth_finetuned")
    a = p.parse_args()
    train(iters=a.iters, servers=a.servers, per_server=a.per_server, rollout=a.rollout, move=a.move, init=a.init, save=a.save)
