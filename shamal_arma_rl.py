#!/usr/bin/env python3
"""shamal_arma_rl.py — A2 : le cerveau obs-Arma (sans coque) atteint-il/depasse-t-il le prof apres RL ?
Recette Shamal : BC (imiter le prof, obs-Arma) -> RL fine-tune (recompense = gagner). Compare au prof held-out."""
import sys, torch, torch.nn as nn, numpy as np, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
from shamal_teacher import shamal_action
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["ronda", "matera", "positano"]; TEST = ["athens", "delphi", "santorini"]; N = 768


def mkenv(name, sd, n=N):
    return AssaultTerrain(num_envs=n, A=9, D=6, R_spawn=115.0, relief=40.0, hit=0.10, shell_obs=False,
                          team_obs=True, suffer=True, postures=True, hull=True, replica=True,
                          replica_path=BASE % name, max_steps=60, device=DEV, seed=sd)


@torch.no_grad()
def rollout(pol):
    r = {"s": [], "d": [], "w": []}
    for mp in TEST:
        e = mkenv(mp, 9000); o = e.reset(); done = torch.zeros(N, dtype=torch.bool, device=DEV)
        for _ in range(90):
            o, _, dn, info = e.step(pol(e, o), auto_reset=False)
            nw = dn.bool() & ~done
            if nw.any():
                r["s"] += (1 - info["losses"][nw]).tolist(); r["d"] += info["dkilled"][nw].tolist(); r["w"] += info["neutralized"][nw].float().tolist()
            done |= dn.bool()
            if bool(done.all()): break
        del e; torch.cuda.empty_cache()
    m = lambda x: sum(x) / len(x) if x else 0.0
    return m(r["w"]), m(r["d"]), m(r["s"])


probe = mkenv(TRAIN[0], 0, 8); O = probe.obs_dim; del probe
net = Net(O, 13, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)

# --- 1) BC : imiter le prof (obs-Arma) ---
print("BC (imiter le prof, obs-Arma %d)..." % O, flush=True)
X, Y = [], []
for i, nm in enumerate(TRAIN):
    e = mkenv(nm, i); o = e.reset()
    for _ in range(60):
        a = shamal_action(e); X.append(o.reshape(-1, O).cpu()); Y.append(a.reshape(-1).cpu()); o, _, _, _ = e.step(a, auto_reset=False)
    del e
X = torch.cat(X).to(DEV); Y = torch.cat(Y).to(DEV); lf = nn.CrossEntropyLoss()
for ep in range(12):
    p = torch.randperm(X.shape[0], device=DEV)
    for i in range(0, X.shape[0], 8192):
        j = p[i:i + 8192]; opt.zero_grad(); lf(net.a_logits(X[j]), Y[j]).backward(); opt.step()
del X, Y; torch.cuda.empty_cache()
bw, bd, bs = rollout(lambda e, o: net.a_logits(o).argmax(-1))
print("  BC-init : win %.3f dkilled %.3f survie %.3f" % (bw, bd, bs), flush=True)

# --- 2) RL fine-tune (recompense = gagner, built-in assault) ---
print("RL fine-tune (24 rounds)...", flush=True)
opt = torch.optim.Adam(net.parameters(), 2e-4)
envs = [mkenv(nm, 100 + i) for i, nm in enumerate(TRAIN)]; obs = [e.reset() for e in envs]
for r in range(24):
    for i, e in enumerate(envs): obs[i] = ppo_iters(net, opt, e, obs[i], 4, O)
    if r % 6 == 0: print("  round %d" % r, flush=True)
del envs; torch.cuda.empty_cache()
rw, rd, rs = rollout(lambda e, o: net.a_logits(o).argmax(-1))
tw, td, ts = rollout(lambda e, o: shamal_action(e))
torch.save(net.state_dict(), "/home/younes/arma3-marl/shamal_arma.pt")

print("\n=== A2 : obs-Arma  BC -> RL  vs  prof (held-out) ===")
print("  prof LAMBS : win %.3f dkilled %.3f survie %.3f" % (tw, td, ts))
print("  BC-init    : win %.3f dkilled %.3f survie %.3f" % (bw, bd, bs))
print("  RL final   : win %.3f dkilled %.3f survie %.3f" % (rw, rd, rs))
print("  -> RL obs-Arma >= prof : %s (win %+.3f)" % ("OUI" if rw >= tw - 0.02 else "non", rw - tw))
print("  sauve shamal_arma.pt")
