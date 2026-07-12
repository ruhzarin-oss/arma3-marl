#!/usr/bin/env python3
"""ow_gauge.py — OVERWATCH / DEFILEMENT : le scenario qui FORCE la verticalite.
Recompense = neutraliser l'ennemi EN RESTANT NON-VU (penalite d'exposition, pas de poussee a l'objectif).
Teste si les 2 pieces parquees en assaut (postures + LOS 2.5D) paient ENFIN ici.
  Bras A = LOS plat, SANS postures  (baseline aveugle a la 3D)
  Bras B = LOS 2.5D + postures       (percoit et exploite la verticalite)
Cartes = villes grecques a flanc de colline (bati sur pente). Defenseurs letaux.
NB gauge : train+eval sur les memes 3 cartes relief (variete = spawns/seeds). Si l'effet apparait -> cartes held-out."""
import sys, argparse, torch, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"
MAPS = ["athens", "delphi", "santorini"]
ARMS = {"A": dict(flat_los=True, postures=False), "B": dict(flat_los=False, postures=True)}

ap = argparse.ArgumentParser()
ap.add_argument("--ne", type=int, default=4000); ap.add_argument("--rounds", type=int, default=15)
ap.add_argument("--K", type=int, default=4); ap.add_argument("--A", type=int, default=9)
ap.add_argument("--D", type=int, default=6); ap.add_argument("--rspawn", type=float, default=90.0)
ap.add_argument("--hit", type=float, default=0.25); ap.add_argument("--owexpo", type=float, default=0.05)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--smoke", action="store_true")
a = ap.parse_args()
if a.smoke: a.ne = 64; a.rounds = 2

def mkenv(name, flat_los, postures, n, sd):
    return AssaultTerrain(num_envs=n, A=a.A, D=a.D, R_spawn=a.rspawn, relief=40.0, hit=a.hit,
                          shell_obs=True, team_obs=True, replica=True, replica_path=BASE % name,
                          max_steps=60, device=DEV, seed=sd, postures=postures, flat_los=flat_los,
                          overwatch=True, ow_expo=a.owexpo)

@torch.no_grad()
def diag(name):
    """PROUVE l'asymetrie AVANT d'entrainer : a positions EGALES, se coucher reduit-il l'exposition ?"""
    e = mkenv(name, False, True, 512, 123); e.reset(); e.hit = 0.0   # degats coupes : on mesure la GEOMETRIE, pas la survie
    HOLD = torch.full((e.N, e.A), 8, device=DEV, dtype=torch.long)
    for _ in range(8):                                      # avancer vers l'objectif (scripted) pour entrer en contact, sans mourir
        th = torch.atan2(-e.apx, -e.apy); act = (torch.round(th / (3.14159 / 4.0)) % 8).long()
        e.step(act, auto_reset=False)
    e.posture[:] = 0; e.step(HOLD, auto_reset=False); es = e.last_exposed.mean().item()   # tout le monde DEBOUT
    e.posture[:] = 2; e.step(HOLD, auto_reset=False); ep = e.last_exposed.mean().item()   # tout le monde COUCHE
    return es, ep

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

print("=== DIAGNOSTIC overwatch : exposition DEBOUT vs COUCHE (memes positions) ===", flush=True)
for m in MAPS:
    es, ep = diag(m)
    print("  %-10s : debout=%.3f  couche=%.3f  reduction=%+.0f%%" % (m, es, ep, 100 * (1 - ep / max(es, 1e-6))), flush=True)

res = {}
print("\n=== ENTRAINEMENT (ne=%d rounds=%d hit=%.2f D=%d rspawn=%.0f owexpo=%.02f) ===" % (a.ne, a.rounds, a.hit, a.D, a.rspawn, a.owexpo), flush=True)
for arm, fl in ARMS.items():
    torch.manual_seed(a.seed)
    probe = mkenv(MAPS[0], fl["flat_los"], fl["postures"], 8, a.seed); O, NA = probe.obs_dim, probe.n_actions; del probe
    net = Net(O, NA, 512, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    envs = [mkenv(nm, fl["flat_los"], fl["postures"], a.ne, a.seed * 100 + i) for i, nm in enumerate(MAPS)]
    obs = [e.reset() for e in envs]
    for _ in range(a.rounds):
        for i, e in enumerate(envs): obs[i] = ppo_iters(net, opt, e, obs[i], a.K, O)
    del envs; torch.cuda.empty_cache()
    metr = {k: [] for k in ("survie", "expo", "dkilled", "win", "posture")}
    for mp in MAPS:                                          # EVAL en 3D reelle (flat_los=False), postures selon le bras
        ev = mkenv(mp, False, fl["postures"], a.ne, 9000 + a.seed); r = evaluate(net, ev)
        for k in metr: metr[k].append(r[k])
        del ev; torch.cuda.empty_cache()
    res[arm] = {k: st.mean(v) for k, v in metr.items()}
    print("  [%s] survie=%.3f expo=%.3f dkilled=%.3f win=%.3f posture=%.2f" %
          (arm, res[arm]["survie"], res[arm]["expo"], res[arm]["dkilled"], res[arm]["win"], res[arm]["posture"]), flush=True)

print("\n=== VERDICT OVERWATCH (B=2.5D+postures  vs  A=plat sans postures) ===", flush=True)
for k in ("survie", "expo", "dkilled", "win"):
    print("  %-8s : A=%.3f  B=%.3f  delta=%+.3f" % (k, res["A"][k], res["B"][k], res["B"][k] - res["A"][k]), flush=True)
print("  usage postures B : %.2f" % res["B"]["posture"], flush=True)
dS = res["B"]["survie"] - res["A"]["survie"]; dE = res["B"]["expo"] - res["A"]["expo"]
turtle_ok = res["B"]["dkilled"] >= res["A"]["dkilled"] - 0.02   # ANTI-TURTLE : B ne doit pas gagner en se planquant
print("  -> B survit plus (>+.10): %s | B moins expose (<-.02): %s | postures utilisees: %s | ANTI-TURTLE (B tue >= A): %s" %
      ("OUI" if dS > 0.10 else "non", "OUI" if dE < -0.02 else "non",
       "OUI" if res["B"]["posture"] > 0.05 else "NON", "OUI" if turtle_ok else "NON !! (B se planque)"), flush=True)
print("  === OVERWATCH VALIDE si les 4 = OUI ===", flush=True)
