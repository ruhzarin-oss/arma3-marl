#!/usr/bin/env python3
"""ab_runner.py — execute l'A/B de PROTOCOL.md.
Bras A = flat_los=True + postures=False (baseline plat, posture-aveugle).
Bras B = flat_los=False + postures=True (2.5D + postures).
Entraine chaque bras sur les 4 villes TRAIN (multi-cartes, meme budget/seeds), evalue sur les
villes TEST (plat + relief) EN 3D REELLE pour les deux (flat_los=False a l'eval, cf PROTOCOL §3).
Metriques : survie(1-losses) / dkilled / win / exposition / usage-postures.
  --smoke  : run minuscule pour prouver le pipeline (1 seed, 1 round, 2 cartes test).
"""
import sys, time, argparse, statistics as st
import torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"
BASE = "/home/younes/arma3-marl/replica_%s.npz"
TRAIN = ["denver", "chicago", "paris", "madrid"]
TEST_FLAT = ["newyork", "london", "lille"]
TEST_RELIEF = ["athens", "delphi", "santorini"]
ARMS = {"A": dict(flat_los=True, postures=False), "B": dict(flat_los=False, postures=False)}

ap = argparse.ArgumentParser()
ap.add_argument("--smoke", action="store_true")
ap.add_argument("--seeds", type=int, default=5)
ap.add_argument("--rounds", type=int, default=15)
ap.add_argument("--K", type=int, default=4)
ap.add_argument("--ne", type=int, default=256)
ap.add_argument("--A", type=int, default=9)
ap.add_argument("--D", type=int, default=4)
ap.add_argument("--rspawn", type=float, default=80.0)
ap.add_argument("--hit", type=float, default=0.10)
ap.add_argument("--out", default="/home/younes/arma3-marl/ab_results.txt")
a = ap.parse_args()
if a.smoke:
    a.seeds, a.rounds, a.K, a.ne = 1, 1, 2, 64
    TESTS = [TEST_FLAT[0], TEST_RELIEF[0]]
else:
    TESTS = TEST_FLAT + TEST_RELIEF
EVAL_NE = 128 if a.smoke else a.ne

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
            surv += (1 - info["losses"][newly]).tolist(); dk += info["dkilled"][newly].tolist()
            neu += info["neutralized"][newly].float().tolist()
        done_once |= d.bool()
        if bool(done_once.all()): break
    m = lambda x: (sum(x) / len(x)) if x else 0.0
    return dict(survie=m(surv), dkilled=m(dk), win=m(neu),
                expo=(exp_acc / exp_n.clamp(min=1)).mean().item(),
                posture=((post_acc / exp_n.clamp(min=1)).mean().item() if env.postures else 0.0))

def train_one(flags, seed):
    probe = mkenv(TRAIN[0], flags["flat_los"], flags["postures"], 8, seed)
    O, NA = probe.obs_dim, probe.n_actions; del probe
    net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    envs = [mkenv(nm, flags["flat_los"], flags["postures"], a.ne, seed * 100 + i) for i, nm in enumerate(TRAIN)]
    obs = [e.reset() for e in envs]
    for _ in range(a.rounds):
        for i, e in enumerate(envs):
            obs[i] = ppo_iters(net, opt, e, obs[i], a.K, O)
    del envs; torch.cuda.empty_cache()
    return net

lines = []
def log(x): print(x, flush=True); lines.append(str(x))
log("=== A/B RUNNER %s | seeds=%d rounds=%d K=%d ne=%d A=%d D=%d rspawn=%.0f | test=%s ===" %
    ("SMOKE" if a.smoke else "FULL", a.seeds, a.rounds, a.K, a.ne, a.A, a.D, a.rspawn, ",".join(TESTS)))
t0 = time.time()
agg = {arm: {mp: {k: [] for k in ("survie", "dkilled", "win", "expo", "posture")} for mp in TESTS} for arm in ARMS}
for arm, flags in ARMS.items():
    for sd in range(a.seeds):
        net = train_one(flags, sd)
        for mp in TESTS:
            ev = mkenv(mp, False, flags["postures"], EVAL_NE, 9000 + sd)   # EVAL = 3D reel pour les 2 bras
            res = evaluate(net, ev); del ev; torch.cuda.empty_cache()
            for k in agg[arm][mp]: agg[arm][mp][k].append(res[k])
        log("  [%s seed %d] entraine+evalue (%.0fs)" % (arm, sd, time.time() - t0))

def pool(arm, maps, k): return [x for mp in maps for x in agg[arm][mp][k]]
def ms(v): return (st.mean(v), (st.pstdev(v) if len(v) > 1 else 0.0)) if v else (0.0, 0.0)
log("\n=== RESULTATS (moyenne +- ecart-type sur %d seed(s)) ===" % a.seeds)
for cat, maps in (("PLAT", [m for m in TESTS if m in TEST_FLAT]), ("RELIEF", [m for m in TESTS if m in TEST_RELIEF])):
    if not maps: continue
    log("--- TEST %s (%s) ---" % (cat, ",".join(maps)))
    for k in ("survie", "expo", "dkilled", "win"):
        (ma, sa), (mb, sb) = ms(pool("A", maps, k)), ms(pool("B", maps, k))
        log("  %-8s : A=%.3f+-%.3f   B=%.3f+-%.3f   delta=%+.3f" % (k, ma, sa, mb, sb, mb - ma))
    pu = pool("B", maps, "posture"); log("  usage postures (B) : %.2f" % (st.mean(pu) if pu else 0))

log("\n=== VERDICT vs seuil PROTOCOL ===")
allm = TESTS
dS = st.mean(pool("B", allm, "survie")) - st.mean(pool("A", allm, "survie"))
gk = st.mean(pool("B", allm, "dkilled")) >= st.mean(pool("A", allm, "dkilled"))
ex = st.mean(pool("B", allm, "expo")) < st.mean(pool("A", allm, "expo"))
log("  survie(B-A) = %+.3f  (seuil >= +0.10) : %s" % (dS, "OUI" if dS >= 0.10 else "non"))
log("  garde-fou dkilled(B)>=dkilled(A) (anti-turtle) : %s" % ("OUI" if gk else "NON"))
log("  exposition(B) < exposition(A) : %s" % ("OUI" if ex else "non"))
log("  -> H1 confirmee" if (dS >= 0.10 and gk and ex) else "  -> H1 non confirmee (ou run trop court)")
open(a.out, "w").write("\n".join(lines) + "\n")
log("\n=> rapport ecrit dans %s" % a.out)
