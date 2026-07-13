"""shamal_eval — le GATE « ≥ LAMBS ».

SHAMAL (BC) doit ÉGALER le prof scripté (LAMBS distillé) pour valider la copie. On compare 3
politiques sur les MÊMES cartes/seeds : le prof scripté, SHAMAL (BC appris), et une baseline
foncer-aveugle. Métriques : win (tout neutralisé), dkilled (fraction tuée), survie.
Verdict = SHAMAL win >= 0.9 x prof win  ->  copie réussie (>= LAMBS).

Pour le VRAI run rigoureux : pointer MAPS vers les cartes HELD-OUT (Athènes/Delphes/Santorin)
et SEEDS sur >=5, exactement comme l'ablation verticalité.
Smoke :  python shamal_eval.py smoke
"""
import sys, math, os
import numpy as np
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from shamal_teacher import shamal_action

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
BASE = "/home/younes/arma3-marl"
ARMA = os.environ.get("SHAMAL_ARMA") == "1"   # SHAMAL_ARMA=1 -> variante obs Arma-cheap
BC = BASE + ("/shamal_arma_bc.pt" if ARMA else "/shamal_bc.pt")
# GATE sur les cartes HELD-OUT (jamais vues à l'entraînement) = généralisation, comme l'ablation
HELD_OUT = [BASE + "/replica_%s.npz" % c for c in ("athens", "delphi", "santorini")]


def mkenv(n, sd, A, D, path):
    return AssaultTerrain(num_envs=n, A=A, D=D, R_spawn=115.0, relief=40.0, hit=0.10,
                          shell_obs=not ARMA, team_obs=True, suffer=True, postures=True, hull=True,
                          arma_obs=ARMA, replica=True, replica_path=path, max_steps=60, device=DEV, seed=sd)


@torch.no_grad()
def rollout(policy, e, steps=70):
    obs = e.reset(); win = part = surv = 0.0; nep = 0
    done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    for _ in range(steps):
        a = policy(e, obs)
        obs, _, done, info = e.step(a, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any():
            win += info["neutralized"][dm].float().sum().item()
            part += info["dkilled"][dm].float().sum().item()
            surv += (1.0 - info["losses"][dm]).sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return win / max(nep, 1), part / max(nep, 1), surv / max(nep, 1)


def pol_teacher(e, obs): return shamal_action(e)
def pol_net(net): return lambda e, obs: net.a_logits(obs).argmax(-1)
def pol_advance(e, obs): return (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4.0)) % 8).long()


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    CKPT = sys.argv[2] if len(sys.argv) > 2 else BC       # arg 2 = checkpoint à noter (défaut shamal_bc.pt ; passer shamal_rl.pt pour la phase 2)
    LBL = "SHAMAL(" + CKPT.split("/")[-1].replace("shamal_", "").replace(".pt", "") + ")"
    A, D = 9, 6
    N = 128 if SMOKE else 1024
    NS = int(sys.argv[3]) if len(sys.argv) > 3 else 5     # arg 3 = nb de seeds (défaut 5 ; plus = IC plus serré)
    SEEDS = [0] if SMOKE else list(range(NS))
    MAPS = HELD_OUT[:1] if SMOKE else HELD_OUT            # smoke = 1 carte ; vrai run = les 3 held-out
    e0 = mkenv(8, 0, A, D, MAPS[0]); O, NA = e0.obs_dim, e0.n_actions; del e0
    net = Net(O, NA, 512, 3).to(DEV)
    net.load_state_dict(torch.load(CKPT, map_location=DEV)); net.eval()
    pols = [("prof LAMBS", pol_teacher), (LBL, pol_net(net)), ("foncer", pol_advance)]
    print("=== SHAMAL eval : gate >= LAMBS  (win / dkilled / survie) SMOKE=%s ===" % SMOKE, flush=True)
    agg = {name: {"win": [], "dk": [], "sv": []} for name, _ in pols}
    permap = {name: {} for name, _ in pols}
    mapname = lambda p: p.split("/")[-1].replace("replica_", "").replace(".npz", "")
    for path in MAPS:
        mn = mapname(path)
        for name, _ in pols: permap[name].setdefault(mn, [])
        for sd in SEEDS:
            for name, pol in pols:
                e = mkenv(N, sd, A, D, path)
                w, p, s = rollout(pol, e)
                agg[name]["win"].append(w); agg[name]["dk"].append(p); agg[name]["sv"].append(s)
                permap[name][mn].append(w)
                del e; torch.cuda.empty_cache()
    print("  (%d seeds x %d cartes)" % (len(SEEDS), len(MAPS)), flush=True)
    for name, _ in pols:
        w = np.array(agg[name]["win"]); p = np.array(agg[name]["dk"]); s = np.array(agg[name]["sv"])
        print("  %-11s | win %.3f±%.3f | dkilled %.3f±%.3f | survie %.3f±%.3f" %
              (name, w.mean(), w.std(), p.mean(), p.std(), s.mean(), s.std()), flush=True)
    print("  --- win PAR CARTE (le detail qui tue le bruit) : prof vs %s ---" % LBL, flush=True)
    won = 0
    for mn in [mapname(p) for p in MAPS]:
        pv = np.mean(permap["prof LAMBS"][mn]); cv = np.mean(permap[LBL][mn])
        tag = "SHAMAL >" if cv > pv else "  prof >"
        won += int(cv > pv)
        print("    %-11s : prof %.3f | %s %.3f   -> %s" % (mn, pv, LBL, cv, tag), flush=True)
    print("    ==> %s bat le prof sur %d/%d cartes" % (LBL, won, len(MAPS)), flush=True)
    tw = np.array(agg["prof LAMBS"]["win"]).mean(); ts = np.array(agg["prof LAMBS"]["win"]).std()
    sw = np.array(agg[LBL]["win"]).mean()
    # ">= LAMBS" = dans le bruit inter-seed du prof (pas un seuil arbitraire) ; "> LAMBS" = dépasse franchement
    if sw > tw + ts:
        verdict = "DEPASSE LAMBS (> prof + 1 ecart-type)"
    elif sw >= tw - ts:
        verdict = "AU NIVEAU DE LAMBS (dans le bruit du prof)"
    else:
        verdict = "SOUS LAMBS"
    print(">>> VERDICT : %s win %.3f vs prof %.3f (+/-%.3f) -> %s" % (LBL, sw, tw, ts, verdict), flush=True)
    print("SHAMAL_EVAL_DONE", flush=True)
