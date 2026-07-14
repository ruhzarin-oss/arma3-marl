#!/usr/bin/env python3
"""shamal_anticip.py — CRITÈRE 2 : SHAMAL+PRÉSAGE bat-il SHAMAL seul ?
Wrapper qui ajoute la prediction PRESAGE (exposition future) a l'obs. 2 bras entraines a l'identique
(env letal, memes cartes) : baseline (obs brute) vs anticip (obs + prediction). Compare win/survie held-out.
smoke: python shamal_anticip.py smoke"""
import numpy as np, torch, torch.nn as nn, sys, statistics as st
torch.backends.cudnn.enabled = False
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["ronda", "matera", "positano"]; TEST = ["athens", "delphi", "santorini"]
Kh = 4
SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
NE = 128 if SMOKE else 1536; ROUNDS = 2 if SMOKE else 28


class GRUp(nn.Module):
    def __init__(s, O, h=128):
        super().__init__(); s.g = nn.GRU(O, h, batch_first=True); s.f = nn.Linear(h, 1)
    def forward(s, x):
        _, hn = s.g(x); return s.f(hn[-1]).squeeze(-1)


def mkbase(name, n, sd):
    return AssaultTerrain(num_envs=n, A=9, D=6, R_spawn=90, relief=40.0, hit=0.25, shell_obs=True,
                          team_obs=True, replica=True, replica_path=BASE % name, max_steps=60, device=DEV, seed=sd)


class AnticipEnv:
    """Ajoute la prediction PRESAGE (1 feature) a l'obs. Interface identique a AssaultTerrain."""
    def __init__(s, base, presage):
        s.e = base; s.p = presage; s.hist = None
        s.obs_dim = base.obs_dim + 1; s.n_actions = base.n_actions; s.N = base.N; s.A = base.A
    def __getattr__(s, k):
        if k == "e": raise AttributeError(k)
        return getattr(s.e, k)
    def _aug(s, o):
        u = o.unsqueeze(2)
        s.hist = u.repeat(1, 1, Kh, 1) if s.hist is None else torch.cat([s.hist[:, :, 1:, :], u], 2)
        with torch.no_grad():
            pred = s.p(s.hist.reshape(s.N * s.A, Kh, -1)).reshape(s.N, s.A, 1)
        return torch.cat([o, pred], -1)
    def reset(s):
        s.hist = None; return s._aug(s.e.reset())
    def step(s, a, auto_reset=True):
        o, r, d, info = s.e.step(a, auto_reset=auto_reset); return s._aug(o), r, d, info


@torch.no_grad()
def evaluate(net, env, n_steps=90):
    o = env.reset(); N = env.N; done = torch.zeros(N, dtype=torch.bool, device=DEV)
    surv, dk, neu = [], [], []
    for _ in range(n_steps):
        o, r, d, info = env.step(net.a_logits(o).argmax(-1), auto_reset=False)
        nw = d.bool() & ~done
        if nw.any():
            surv += (1 - info["losses"][nw]).tolist(); dk += info["dkilled"][nw].tolist(); neu += info["neutralized"][nw].float().tolist()
        done |= d.bool()
        if bool(done.all()): break
    m = lambda x: sum(x) / len(x) if x else 0.0
    return m(surv), m(dk), m(neu)


def run(anticip, presage):
    def wrap(b): return AnticipEnv(b, presage) if anticip else b
    e0 = wrap(mkbase(TRAIN[0], 8, 0)); O, NA = e0.obs_dim, e0.n_actions; del e0
    torch.manual_seed(0); net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    envs = [wrap(mkbase(nm, NE, 100 + i)) for i, nm in enumerate(TRAIN)]
    obs = [e.reset() for e in envs]
    for _ in range(ROUNDS):
        for i, e in enumerate(envs): obs[i] = ppo_iters(net, opt, e, obs[i], 4, O)
    del envs; torch.cuda.empty_cache()
    r = {"surv": [], "dk": [], "win": []}
    for mp in TEST:
        ev = wrap(mkbase(mp, NE, 9000)); s, d_, w = evaluate(net, ev); del ev; torch.cuda.empty_cache()
        r["surv"].append(s); r["dk"].append(d_); r["win"].append(w)
    return {k: st.mean(v) for k, v in r.items()}


d = np.load("/home/younes/arma3-marl/presage_data.npz"); Op = int(d["O"])
presage = GRUp(Op).to(DEV); presage.load_state_dict(torch.load("/home/younes/arma3-marl/presage.pt", map_location=DEV)); presage.eval()
print("PRESAGE charge (obs %d). Entrainement 2 bras (ne=%d rounds=%d)..." % (Op, NE, ROUNDS), flush=True)
A = run(False, presage); print("  baseline   : win %.3f  dkilled %.3f  survie %.3f" % (A["win"], A["dk"], A["surv"]), flush=True)
B = run(True, presage); print("  +PRESAGE   : win %.3f  dkilled %.3f  survie %.3f" % (B["win"], B["dk"], B["surv"]), flush=True)
print("\n=== CRITERE 2 (held-out) ===")
for k, lbl in (("win", "win"), ("surv", "survie"), ("dk", "dkilled")):
    print("  %-8s : baseline %.3f  +PRESAGE %.3f  delta %+.3f" % (lbl, A[k], B[k], B[k] - A[k]))
print("  -> SHAMAL+PRESAGE bat SHAMAL seul : %s" % ("OUI" if B["win"] > A["win"] + 0.01 or B["surv"] > A["surv"] + 0.02 else "non"), flush=True)
