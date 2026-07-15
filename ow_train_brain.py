#!/usr/bin/env python3
"""ow_train_brain.py — ETAPE 5 / T2 : entraine ET SAUVE un cerveau decideur de posture dans le
sandbox overwatch, pour le brancher ensuite sur le G1. Deux variantes a comparer :
  --arm knob      : hull-down (profil par posture) -> apprend a s'accroupir quand expose
  --arm emergent  : exposition geometrique (M rayons) -> sans knob
Sauve le .pt + rapporte l'usage des postures (decide-t-il vraiment de se baisser ?)."""
import sys, argparse, torch, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["ronda", "matera", "positano", "sarajevo"]
TEST = ["athens", "delphi", "santorini"]
ARMS = {
    "knob":     dict(flat_los=False, postures=True, hull=True,  emergent=False),
    "emergent": dict(flat_los=False, postures=True, hull=False, emergent=True),
}
ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True, choices=list(ARMS))
ap.add_argument("--ne", type=int, default=2000); ap.add_argument("--rounds", type=int, default=22)
ap.add_argument("--K", type=int, default=4); ap.add_argument("--A", type=int, default=9)
ap.add_argument("--D", type=int, default=6); ap.add_argument("--rspawn", type=float, default=90.0)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--out", default=None)
a = ap.parse_args(); fl = ARMS[a.arm]

def mkenv(name, n, sd, evalmode=False):
    return AssaultTerrain(num_envs=n, A=a.A, D=a.D, R_spawn=a.rspawn, relief=40.0, hit=a.hit,
                          shell_obs=True, team_obs=True, replica=True, replica_path=BASE % name, max_steps=60,
                          device=DEV, seed=sd, postures=True, flat_los=(False if evalmode else fl["flat_los"]),
                          overwatch=True, hull=fl["hull"], ow_dmg=0.3, ow_tofail=0.5, emergent_expo=fl["emergent"])

@torch.no_grad()
def evaluate(net, env, n_steps=90):
    o = env.reset(); N = env.N
    done = torch.zeros(N, dtype=torch.bool, device=DEV)
    post = torch.zeros(N, device=DEV); nn_ = torch.zeros(N, device=DEV); surv, dk, neu = [], [], []
    for _ in range(n_steps):
        act = net.a_logits(o).argmax(-1)
        o, r, d, info = env.step(act, auto_reset=False)
        live = (~done).float(); post += (env.posture > 0).float().mean(1) * live; nn_ += live
        newly = d.bool() & ~done
        if newly.any():
            surv += (1 - info["losses"][newly]).tolist(); dk += info["dkilled"][newly].tolist(); neu += info["neutralized"][newly].float().tolist()
        done |= d.bool()
        if bool(done.all()): break
    m = lambda x: (sum(x) / len(x)) if x else 0.0
    return m(surv), m(dk), m(neu), (post / nn_.clamp(min=1)).mean().item()

torch.manual_seed(a.seed)
probe = mkenv(TRAIN[0], 8, a.seed); O, NA = probe.obs_dim, probe.n_actions; del probe
print("[T2:%s] obs_dim=%d n_actions=%d -> entrainement (ne=%d rounds=%d)" % (a.arm, O, NA, a.ne, a.rounds), flush=True)
net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
envs = [mkenv(nm, a.ne, a.seed * 100 + i) for i, nm in enumerate(TRAIN)]
obs = [e.reset() for e in envs]
for r in range(a.rounds):
    for i, e in enumerate(envs): obs[i] = ppo_iters(net, opt, e, obs[i], a.K, O)
    if r % 5 == 0: print("  round %d/%d" % (r, a.rounds), flush=True)
del envs; torch.cuda.empty_cache()

out = a.out or ("/home/younes/arma3-marl/brain_%s.pt" % a.arm)
torch.save({"state_dict": net.state_dict(), "obs_dim": O, "n_actions": NA, "arm": a.arm}, out)
print("[T2:%s] SAUVE -> %s" % (a.arm, out), flush=True)

res = {k: [] for k in ("surv", "dk", "win", "post")}
for mp in TEST:
    ev = mkenv(mp, a.ne, 9000, evalmode=True); s, d_, w, p = evaluate(net, ev); del ev; torch.cuda.empty_cache()
    for k, v in zip(res, (s, d_, w, p)): res[k].append(v)
print("[T2:%s] EVAL (held-out) : survie=%.2f dkilled=%.2f win=%.2f  USAGE POSTURES=%.2f" %
      (a.arm, st.mean(res["surv"]), st.mean(res["dk"]), st.mean(res["win"]), st.mean(res["post"])), flush=True)
print("  -> decide de se baisser : %s" % ("OUI" if st.mean(res["post"]) > 0.15 else "NON (reste debout)"), flush=True)
