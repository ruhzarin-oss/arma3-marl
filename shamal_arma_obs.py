#!/usr/bin/env python3
"""shamal_arma_obs.py — BRIQUE 1 jambe ARMA : le cerveau tient-il avec l'obs LEGERE qu'Arma peut donner
cheap (LOS native, SANS la coque a 12 rayons) ? On imite le prof (BC) avec obs-Arma (shell_obs=False)
vs obs complete, et on compare au prof sur cartes held-out. Si obs-Arma ~ prof -> deployable dans Arma."""
import sys, torch, torch.nn as nn, numpy as np, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from shamal_teacher import shamal_action
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["ronda", "matera", "positano"]; TEST = ["athens", "delphi", "santorini"]; N = 512


def mkenv(name, shell, sd):
    return AssaultTerrain(num_envs=N, A=9, D=6, R_spawn=115.0, relief=40.0, hit=0.10, shell_obs=shell,
                          team_obs=True, suffer=True, postures=True, hull=True, replica=True,
                          replica_path=BASE % name, max_steps=60, device=DEV, seed=sd)


@torch.no_grad()
def collect(shell):
    X, Y = [], []
    for i, nm in enumerate(TRAIN):
        e = mkenv(nm, shell, i); o = e.reset()
        for _ in range(60):
            a = shamal_action(e)
            X.append(o.reshape(-1, o.shape[-1]).cpu()); Y.append(a.reshape(-1).cpu())
            o, _, _, _ = e.step(a, auto_reset=False)
    return torch.cat(X), torch.cat(Y)


@torch.no_grad()
def rollout(pol, name, shell):
    r = {"s": [], "d": [], "w": []}
    for mp in TEST:
        e = mkenv(mp, shell, 9000); o = e.reset(); done = torch.zeros(N, dtype=torch.bool, device=DEV)
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


def bc(shell, lbl):
    X, Y = collect(shell); O = X.shape[1]; NA = int(Y.max()) + 1
    X, Y = X.to(DEV), Y.to(DEV)
    net = Net(O, 13, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 1e-3); lf = nn.CrossEntropyLoss()
    for ep in range(12):
        p = torch.randperm(X.shape[0], device=DEV)
        for i in range(0, X.shape[0], 8192):
            j = p[i:i + 8192]; opt.zero_grad(); lf(net.a_logits(X[j]), Y[j]).backward(); opt.step()
    net.eval()
    acc = (net.a_logits(X).argmax(-1) == Y).float().mean().item()
    w, d, s = rollout(lambda e, o: net.a_logits(o).argmax(-1), lbl, shell)
    print("  %-16s obs_dim=%2d | imite prof %.0f%% | win %.3f dkilled %.3f survie %.3f" % (lbl, O, 100 * acc, w, d, s), flush=True)
    return w, d, s


print("=== prof (reference) ===", flush=True)
tw, td, ts = rollout(lambda e, o: shamal_action(e), "prof", True)
print("  %-16s              | win %.3f dkilled %.3f survie %.3f" % ("prof LAMBS", tw, td, ts), flush=True)
print("=== BC : obs complete vs obs-ARMA (sans coque) ===", flush=True)
bc(True, "BC obs complete")
aw, ad, as_ = bc(False, "BC obs-ARMA")
print("\n=== VERDICT jambe Arma ===")
print("  obs-Arma vs prof : win %+.3f | survie %+.3f" % (aw - tw, as_ - ts))
print("  -> le cerveau tient sans la coque (deployable Arma) : %s" % ("OUI" if aw >= tw - 0.05 else "la coque compte"))
