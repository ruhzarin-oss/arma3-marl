"""③.3.2/3.3 — SELF-PLAY DANS ARMA. Wrapper multi-serveurs (M ArmaEnvSelfPlay en parallele) + double
entrainement (deux politiques BLU/OPF, MAPPO feedforward), warm-start depuis le self-play toy.
Les deux escouades APPRENNENT en s'affrontant dans le vrai jeu."""
import time, argparse, threading, os, csv
import numpy as np
import torch, torch.nn as nn
from datetime import datetime
from torch.distributions import Categorical
from train_mem import FF
from train_harmattan import desktop_root

SB = "/mnt/data/harmattan-sandbox"


class MultiSelfPlay:
    def __init__(self, num_servers=12, per_server=4, **kw):
        from arma_env_selfplay import ArmaEnvSelfPlay
        self.envs = [ArmaEnvSelfPlay(num_envs=per_server,
                                     mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % i,
                                     log=SB + "/logs/server%d.out" % i, seed=i, **kw) for i in range(num_servers)]
        self.n_actions = self.envs[0].n_actions; self.obs_dim = self.envs[0].obs_dim; self.A = self.envs[0].A
        self.sizes = [e.N for e in self.envs]; self.N = sum(self.sizes); self._sp = np.cumsum(self.sizes)[:-1]

    def _par(self, fns):
        res = [None] * len(self.envs); th = []
        for i in range(len(self.envs)):
            t = threading.Thread(target=lambda i=i: res.__setitem__(i, fns[i]())); t.start(); th.append(t)
        for t in th: t.join()
        return res

    def reset(self):
        r = self._par([(lambda e=e: e.reset()) for e in self.envs])
        return np.concatenate([x[0] for x in r], 0), np.concatenate([x[1] for x in r], 0)

    def step(self, a0, a1):
        p0 = np.split(a0, self._sp, 0); p1 = np.split(a1, self._sp, 0)
        r = self._par([(lambda e=self.envs[i], x=p0[i], y=p1[i]: e.step(x, y)) for i in range(len(self.envs))])
        o0 = np.concatenate([x[0] for x in r], 0); o1 = np.concatenate([x[1] for x in r], 0)
        rw0 = np.concatenate([x[2] for x in r], 0); rw1 = np.concatenate([x[3] for x in r], 0)
        done = np.concatenate([x[4] for x in r], 0)
        info = {k: np.concatenate([x[5][k] for x in r], 0) for k in ("win0", "win1", "decided")}
        return o0, o1, rw0, rw1, done, info


def ppo(net, opt, B, lastv, cfg, dev):
    T, N = B["rew"].shape; gamma, lam = cfg["gamma"], cfg["gae"]
    adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
    for t in reversed(range(T)):
        nnt = 1 - B["done"][t]; nv = lastv if t == T - 1 else B["val"][t + 1]
        delta = B["rew"][t] + gamma * nv * nnt - B["val"][t]; g = delta + gamma * lam * nnt * g; adv[t] = g
    ret = (adv + B["val"]).reshape(T * N); an = (adv - adv.mean()) / (adv.std() + 1e-8)
    A = B["act"].shape[2]; O = B["obs"].shape[3]
    fo = B["obs"].reshape(T * N, A, O); fa = B["act"].reshape(T * N, A); fl = B["logp"].reshape(T * N, A); fad = an.reshape(T * N, 1)
    for _ in range(cfg["epochs"]):
        d = Categorical(logits=net.a_logits(fo)); nlp = d.log_prob(fa); ratio = torch.exp(nlp - fl)
        pl = -torch.min(ratio * fad, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * fad).mean()
        vl = ((net.value(fo) - ret) ** 2).mean(); e = d.entropy().mean()
        loss = pl + cfg["vf"] * vl - cfg["ent"] * e
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()


def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    run_dir = os.path.join(desktop_root(), "Harmattan-entrainements", "run_arenaselfplay_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(run_dir, exist_ok=True); print("[run self-play Arma] %s | device=%s" % (run_dir, dev))
    env = MultiSelfPlay(num_servers=cfg["servers"], per_server=cfg["envs"], step_wait=cfg["step_wait"], settle=cfg["settle"])
    o0, o1 = env.reset(); N, A, O = o0.shape; print("env pret: N=%d A=%d O=%d" % (N, A, O))
    net0 = FF(O, env.n_actions, A, 64).to(dev); net1 = FF(O, env.n_actions, A, 64).to(dev)
    for net, path in ((net0, cfg["init0"]), (net1, cfg["init1"])):
        if path and os.path.exists(path):
            net.load_state_dict(torch.load(path, map_location=dev)); print("WARM-START", path)
    opt0 = torch.optim.Adam(net0.parameters(), lr=cfg["lr"]); opt1 = torch.optim.Adam(net1.parameters(), lr=cfg["lr"])
    cf = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=cfg["epochs"], vf=0.5, ent=cfg["ent"]); T = cfg["rollout"]
    o0t = torch.as_tensor(o0, dtype=torch.float32, device=dev); o1t = torch.as_tensor(o1, dtype=torch.float32, device=dev)
    w0 = []; w1 = []; dec = []; gstep = 0; t0 = time.time(); hist = []
    for it in range(cfg["iters"]):
        Bs = {s: dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                      logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                      val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev)) for s in (0, 1)}
        for t in range(T):
            with torch.no_grad():
                d0 = Categorical(logits=net0.a_logits(o0t)); a0 = d0.sample(); lp0 = d0.log_prob(a0); v0 = net0.value(o0t)
                d1 = Categorical(logits=net1.a_logits(o1t)); a1 = d1.sample(); lp1 = d1.log_prob(a1); v1 = net1.value(o1t)
            no0, no1, r0, r1, done, info = env.step(a0.cpu().numpy(), a1.cpu().numpy())
            for s, (ot, a, lp, v, r) in ((0, (o0t, a0, lp0, v0, r0)), (1, (o1t, a1, lp1, v1, r1))):
                Bs[s]["obs"][t] = ot; Bs[s]["act"][t] = a; Bs[s]["logp"][t] = lp; Bs[s]["val"][t] = v
                Bs[s]["rew"][t] = torch.as_tensor(r, device=dev); Bs[s]["done"][t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]:
                if info["decided"][n]: w0.append(float(info["win0"][n])); w1.append(float(info["win1"][n])); dec.append(1.0)
                else: dec.append(0.0)
            o0t = torch.as_tensor(no0, dtype=torch.float32, device=dev); o1t = torch.as_tensor(no1, dtype=torch.float32, device=dev); gstep += N
        with torch.no_grad():
            lv0 = net0.value(o0t); lv1 = net1.value(o1t)
        ppo(net0, opt0, Bs[0], lv0, cf, dev); ppo(net1, opt1, Bs[1], lv1, cf, dev)
        tm = lambda x: float(np.mean(x[-1500:])) if x else 0.0
        row = dict(iter=it, steps=gstep, blu_win=tm(w0), opf_win=tm(w1), decided=tm(dec), tps=gstep / (time.time() - t0))
        hist.append(row)
        print("it %4d | steps %7d | BLU %.2f | OPF %.2f | decidees %.2f | %.1f tr/s | %.0fs"
              % (it, gstep, row["blu_win"], row["opf_win"], row["decided"], row["tps"], time.time() - t0))
        if it % 5 == 0 or it == cfg["iters"] - 1:
            torch.save(net0.state_dict(), os.path.join(run_dir, "blu.pt")); torch.save(net1.state_dict(), os.path.join(run_dir, "opf.pt"))
            with open(os.path.join(run_dir, "history.csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    print("[fini] %s | BLU %.2f / OPF %.2f / decidees %.2f" % (run_dir, tm(w0), tm(w1), tm(dec)))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("servers", 12, int), ("envs", 4, int), ("iters", 50, int), ("rollout", 14, int),
                    ("lr", 3e-4, float), ("epochs", 4, int), ("ent", 0.02, float), ("step_wait", 2.4, float), ("settle", 0.6, float)]:
        p.add_argument("--" + k.replace("_", "-"), default=v, type=t, dest=k)
    p.add_argument("--init0", default="selfplay_blu.pt"); p.add_argument("--init1", default="selfplay_opf.pt")
    a = p.parse_args(); train(vars(a))
