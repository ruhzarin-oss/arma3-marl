"""officer_geo — BOUCLE ADAPTATIVE. Lit la geometrie (100%) -> manoeuvre championne -> execute. vs M2 fixe.
SOCLE PROPRE (13/06) : RÉUTILISE un env/pont par serveur (re-spawn par op) -> 1 seule connexion/serveur
(anti-timeout, cause prouvee : la 2e connexion a un serveur echoue) + `deleteGroup` au spawn (anti-fuite groupes)."""
import json
import numpy as np, torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
from enemy_profiles import apply_profile, PRO_SKILL_SQF, metrics_dyn
from geometries import GEOMETRIES, OBJ
import maneuvers as M
from collect_geo_recon import geo_features, FEATS, GEOS, SH

SB = "/mnt/data/harmattan-sandbox"
DEV = "cuda:0"
CHAMPION = {"standard": "M8", "concentre": "M5", "disperse": "M2", "faible_ouest": "M1", "faible_est": "M1"}
BEST_FIXED = "M2"


def _load_classifier(path="geo_recon.jsonl"):
    rows = [json.loads(l) for l in open(path) if "disp" in json.loads(l)]
    X = np.array([[float(r[k]) for k in FEATS] for r in rows]); y = np.array([r["geo"] for r in rows])
    mu = X.mean(0); sd = X.std(0) + 1e-9
    cents = {g: ((X[y == g] - mu) / sd).mean(0) for g in GEOS if (y == g).any()}
    return mu, sd, cents


MU, SD, CENTS = _load_classifier()


def classify_geo(feat):
    z = (np.array([float(feat[k]) for k in FEATS]) - MU) / SD
    return min(CENTS, key=lambda g: float(np.linalg.norm(z - CENTS[g])))


def make_env(srv, seed=0):
    """UN env/pont par serveur, a RÉUTILISER pour toutes ses ops (1 connexion/serveur, anti-timeout)."""
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    return OpArma(squads=M.SQUADS, mission=mis, log=log, move=36, seed=seed)


def respawn(env, geo, seed=None):
    """Re-spawn le monde sur un env EXISTANT (réutilise le pont). Renvoie garrison."""
    if seed is not None:
        env.rng = np.random.default_rng(seed)
    garrison, prof = apply_profile(env, "skilled", GEOMETRIES[geo])
    env.spawn(M.SPAWNS, garrison)
    env.b.send(PRO_SKILL_SQF, wait=True)
    return garrison


def _brain():
    b = Net(10, 4, 512, 3).to(DEV); b.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); b.eval(); return b


def run_adaptive(env, garrison, true_geo, brain, max_wall=900, stall_wall=400):
    feat = geo_features(env)
    pred = classify_geo(feat) if feat else "standard"
    man = CHAMPION[pred]
    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = garrison[0][2]
    r = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
    r.run(max_steps=500, max_wall=max_wall, stall_wall=stall_wall)
    m = metrics_dyn(env, r, garrison)
    m["pred_geo"] = pred; m["true_geo"] = true_geo; m["man"] = man; m["reco_ok"] = (pred == true_geo)
    return m


def run_fixed(env, garrison, true_geo, brain, man=BEST_FIXED, max_wall=900, stall_wall=400):
    geo_features(env)
    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = garrison[0][2]
    r = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
    r.run(max_steps=500, max_wall=max_wall, stall_wall=stall_wall)
    m = metrics_dyn(env, r, garrison); m["man"] = man; m["true_geo"] = true_geo
    return m


def close_env(env):
    try:
        env.b.sock.close()
    except Exception:
        pass


if __name__ == "__main__":
    # SMOKE : UN env reutilise sur srv 0, re-spawn par geometrie
    brain = _brain(); env = make_env(0, 800)
    print("=== SMOKE boucle adaptative (env reutilise, 1 pont) ===")
    print("%-13s %-8s %-7s %-5s %s" % ("vraie_geo", "lue", "manoeuv", "reco", "mil"))
    for g in GEOS:
        garrison = respawn(env, g, 800)
        m = run_adaptive(env, garrison, g, brain)
        print("%-13s %-8s %-7s %-5s %s" % (g, m["pred_geo"], m["man"], "OK" if m["reco_ok"] else "X", m["mil"]))
    close_env(env)
