#!/usr/bin/env python3
"""ow_worker.py — UN (bras, seed) de l'ablation OVERWATCH. Entraine sur les 4 cartes relief TRAIN,
evalue sur les 3 cartes relief HELD-OUT (3D reelle, flat_los=False), ecrit un JSON. Lance par ow_ablation.py.
5 bras -> ablation 2x2 (LOS 2.5D x corps hull-down) + un bras hull ATTENUE (robustesse)."""
import sys, json, argparse, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["ronda", "matera", "positano", "sarajevo"]     # relief, entrainement
TEST = ["athens", "delphi", "santorini"]                # relief, HELD-OUT
ARMS = {
    "flat_none":  dict(flat_los=True,  postures=False, hull=False, expose=None),           # baseline aveugle
    "los25_none": dict(flat_los=False, postures=False, hull=False, expose=None),           # LOS 2.5D SEUL
    "flat_hull":  dict(flat_los=True,  postures=True,  hull=True,  expose=None),           # hull-down SEUL (LOS aveugle)
    "full":       dict(flat_los=False, postures=True,  hull=True,  expose=None),           # 2.5D + hull (gagnant)
    "full_mild":  dict(flat_los=False, postures=True,  hull=True,  expose=[1.0, 0.7, 0.5]),# hull ATTENUE (increvable ?)
}
ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True); ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--ne", type=int, default=1024); ap.add_argument("--rounds", type=int, default=18)
ap.add_argument("--K", type=int, default=4); ap.add_argument("--A", type=int, default=9)
ap.add_argument("--D", type=int, default=6); ap.add_argument("--rspawn", type=float, default=90.0)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--owdmg", type=float, default=0.3)
ap.add_argument("--owtofail", type=float, default=0.5); ap.add_argument("--out", required=True)
a = ap.parse_args(); fl = ARMS[a.arm]

def mkenv(name, n, sd, evalmode=False):
    return AssaultTerrain(num_envs=n, A=a.A, D=a.D, R_spawn=a.rspawn, relief=40.0, hit=a.hit,
                          shell_obs=True, team_obs=True, replica=True, replica_path=BASE % name, max_steps=60,
                          device=DEV, seed=sd, postures=fl["postures"],
                          flat_los=(False if evalmode else fl["flat_los"]),
                          overwatch=True, hull=fl["hull"], ow_dmg=a.owdmg, ow_tofail=a.owtofail, expose_lut=fl["expose"])

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

torch.manual_seed(a.seed)
probe = mkenv(TRAIN[0], 8, a.seed); O, NA = probe.obs_dim, probe.n_actions; del probe
net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
envs = [mkenv(nm, a.ne, a.seed * 100 + i) for i, nm in enumerate(TRAIN)]
obs = [e.reset() for e in envs]
for _ in range(a.rounds):
    for i, e in enumerate(envs): obs[i] = ppo_iters(net, opt, e, obs[i], a.K, O)
del envs; torch.cuda.empty_cache()
res = {}
for mp in TEST:
    ev = mkenv(mp, a.ne, 9000 + a.seed, evalmode=True); res[mp] = evaluate(net, ev); del ev; torch.cuda.empty_cache()
json.dump(dict(arm=a.arm, seed=a.seed, results=res), open(a.out, "w"))
print("[%s seed %d] fini" % (a.arm, a.seed))
