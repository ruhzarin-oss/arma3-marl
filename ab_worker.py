#!/usr/bin/env python3
"""ab_worker.py — UN seul (bras, seed) de l'A/B : entraine sur les 4 cartes train, evalue sur
les 6 test en 3D reelle (flat_los=False), ecrit un JSON. Lance en parallele par ab_parallel.py."""
import sys, json, argparse, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["denver", "chicago", "paris", "madrid"]
TESTS = ["newyork", "london", "lille", "athens", "delphi", "santorini"]
ARMS = {"A": dict(flat_los=True, postures=False), "B": dict(flat_los=False, postures=True)}

ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True); ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--ne", type=int, default=1024); ap.add_argument("--rounds", type=int, default=20)
ap.add_argument("--K", type=int, default=4); ap.add_argument("--A", type=int, default=9)
ap.add_argument("--D", type=int, default=6); ap.add_argument("--rspawn", type=float, default=60.0)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--out", required=True)
a = ap.parse_args()
flags = ARMS[a.arm]

def mkenv(name, flat_los, postures, n, sd):
    return AssaultTerrain(num_envs=n, A=a.A, D=a.D, R_spawn=a.rspawn, relief=40.0, hit=a.hit,
                          shell_obs=True, team_obs=True, replica=True, replica_path=BASE % name,
                          max_steps=60, device=DEV, seed=sd, postures=postures, flat_los=flat_los)

@torch.no_grad()
def evaluate(net, env, n_steps=90):
    o = env.reset(); N = env.N
    done_once = torch.zeros(N, dtype=torch.bool, device=DEV)
    exp_acc = torch.zeros(N, device=DEV); exp_n = torch.zeros(N, device=DEV); post_acc = torch.zeros(N, device=DEV)
    surv, dk, neu = [], [], []
    for _ in range(n_steps):
        act = net.a_logits(o).argmax(-1)
        o, r, d, info = env.step(act, auto_reset=False)
        live = (~done_once).float()
        exp_acc += info["exposed"] * live; exp_n += live
        if env.postures: post_acc += (env.posture > 0).float().mean(1) * live
        newly = d.bool() & ~done_once
        if newly.any():
            surv += (1 - info["losses"][newly]).tolist(); dk += info["dkilled"][newly].tolist(); neu += info["neutralized"][newly].float().tolist()
        done_once |= d.bool()
        if bool(done_once.all()): break
    m = lambda x: (sum(x) / len(x)) if x else 0.0
    return dict(survie=m(surv), dkilled=m(dk), win=m(neu),
                expo=(exp_acc / exp_n.clamp(min=1)).mean().item(),
                posture=((post_acc / exp_n.clamp(min=1)).mean().item() if env.postures else 0.0))

probe = mkenv(TRAIN[0], flags["flat_los"], flags["postures"], 8, a.seed)
O, NA = probe.obs_dim, probe.n_actions; del probe
net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
envs = [mkenv(nm, flags["flat_los"], flags["postures"], a.ne, a.seed * 100 + i) for i, nm in enumerate(TRAIN)]
obs = [e.reset() for e in envs]
for _ in range(a.rounds):
    for i, e in enumerate(envs): obs[i] = ppo_iters(net, opt, e, obs[i], a.K, O)
del envs; torch.cuda.empty_cache()
res = {}
for mp in TESTS:
    ev = mkenv(mp, False, flags["postures"], a.ne, 9000 + a.seed); res[mp] = evaluate(net, ev); del ev; torch.cuda.empty_cache()
json.dump(dict(arm=a.arm, seed=a.seed, results=res), open(a.out, "w"))
print("[%s seed %d] fini -> %s" % (a.arm, a.seed, a.out))
