"""officer_live — JALON 1.3/1.4/1.5 (+ 1.1-bis reconnaissance) : operation COMMANDEE PAR L'OFFICIER dans Arma.
SONDE DIRECTIONNELLE (effort principal ouest, pour PROVOQUER la reaction ennemie ; photo avant/apres) ->
RAPPORT = la REACTION en clair -> officier (qwen) DECIDE -> execute -> RE-DECIDE si echec. Journal d'ordres."""
import time, json, argparse
import numpy as np, torch
from op_arma import OpArma, OperationRunner, STANCES
from train_koth_gpu import Net
from enemy_profiles import apply_profile, metrics_dyn, PRO_SKILL_SQF, HUNT_SQF, REACTIVE_DEF_SQF, REACTIVE_DEPTH_SQF, DEFENSE_SQF, ENEMY_PROFILES
from geometries import GEOMETRIES
import maneuvers as M
import officer_op

SB = "/mnt/data/harmattan-sandbox"
DEV = "cuda:0"
POSTURES = ["skilled", "skilled_react", "skilled_react_depth", "skilled_mobile",
            "skilled_elastic", "skilled_herisson", "skilled_appat", "skilled_sortie"]


def enemy_stats(env):
    """Photo de l'ennemi vivant : centroide, occupation de l'objectif, dispersion. None si plus personne."""
    al = env.en_alive()
    if env.en_n == 0 or not al.any():
        return None
    gx, gy = env.base
    ex, ey = env.epx[al], env.epy[al]
    d = np.sqrt((ex - gx) ** 2 + (ey - gy) ** 2)
    return {"n": int(al.sum()), "cx": float(ex.mean()), "cy": float(ey.mean()),
            "in_obj": int((d < 35).sum()), "disp": float(d.mean()), "out60": int((d > 60).sum())}


def _act(env, brain, si):
    o = torch.as_tensor(env.obs(si), dtype=torch.float32, device=DEV)
    with torch.no_grad():
        lg = brain.a_logits(o) + torch.as_tensor(STANCES[env.stances[si]], device=DEV)
    return torch.distributions.Categorical(logits=lg).sample().cpu().numpy()


def interpret(env, s0, s1):
    """Traduit la REACTION ennemie (avant->apres sonde) en phrases mappables sur une posture (signal, pas photo)."""
    gx, gy = env.base
    if s1 is None or s1["n"] == 0:
        return "Au contact, l'ennemi a entierement quitte ses positions (objectif vide)."
    L = []
    # 1) l'objectif s'est-il VIDE ? (appat)
    if s0 and s0["in_obj"] >= 3 and s1["in_obj"] <= 1:
        L.append("L'ennemi occupait l'objectif et l'a ABANDONNE sous notre approche, se repositionnant plus loin.")
    elif s1["in_obj"] == 0:
        L.append("L'ennemi n'est PAS sur l'objectif.")
    else:
        L.append("L'ennemi tient l'objectif (%d unites)." % s1["in_obj"])
    # 2) densite / ecran (herisson)
    if s1["out60"] == 0 and s1["disp"] < 45:
        L.append("Tout l'ennemi est masse en perimetre DENSE dans l'objectif, aucun ecran de patrouilles dehors.")
    elif s0:
        dy = s1["cy"] - s0["cy"]; dx = s1["cx"] - s0["cx"]
        if dy < -22:
            L.append("Sous notre poussee, l'ennemi est VENU vers nos lignes / nos zones de rassemblement (il sort et contre-attaque).")
        elif dy > 22:
            L.append("Sous notre poussee, l'ennemi a RECULE par bonds vers l'arriere (il decroche, ne tient pas sa ligne).")
        elif dx < -18:
            L.append("L'ennemi a deplace ses patrouilles et s'est MASSE sur le flanc OUEST que nous menacons.")
        else:
            L.append("L'ennemi reste fixe : garnison statique avec un ecran de patrouilles, peu de manoeuvre.")
    return " ".join(L)


def setup_op(srv, seed, enemy):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=M.SQUADS, mission=mis, log=log, move=36, seed=seed)
    garrison, prof = apply_profile(env, enemy, GEOMETRIES["standard"])
    env.spawn(M.SPAWNS, garrison)
    sqf = ""
    if prof["pro"]:
        sqf += PRO_SKILL_SQF + (HUNT_SQF if prof.get("hunt", True) else "")
        sqf += REACTIVE_DEF_SQF if prof.get("react") else ""
        sqf += REACTIVE_DEPTH_SQF if prof.get("react_depth") else ""
        if prof.get("def_sqf"):
            sqf += DEFENSE_SQF[prof["def_sqf"]]
    if sqf:
        env.b.send(sqf, wait=True)
    return env, garrison, prof


def probe(env, brain, settle=10, steps=14):
    """Sonde : (1) SETTLE = on attend que l'ennemi se DEPLOIE dans sa posture (s0 = pre-reaction),
    (2) POUSSEE directionnelle ouest pour provoquer la reaction (s1). Renvoie (rapport, s0, s1)."""
    # phase settle : les escouades tiennent loin, l'ennemi se met en place
    for sq in env.squads:
        si = env.squads.index(sq); env.stances[si] = "hold"
    for _ in range(settle):
        env.step([_act(env, brain, si) for si in range(env.S)])
    s0 = enemy_stats(env)
    # poussee : effort principal ouest pour provoquer la reaction
    push = {"SQ_APPUI": (M.CRETE, "suppress"), "SQ_A_OUEST": (M.FLANC_O, "move"),
            "SQ_A_EST": (M.LIGNE_E, "move"), "SQ_RESERVE": (M.POSTE_RES, "hold")}
    for sq, (g, st) in push.items():
        si = env.squads.index(sq); env.goals[si] = np.array(g, dtype=float); env.stances[si] = st
    for _ in range(steps):
        env.step([_act(env, brain, si) for si in range(env.S)])
    s1 = enemy_stats(env)
    return "Sonde effectuee (effort principal a l'ouest). " + interpret(env, s0, s1), s0, s1


def static_report(env, note=""):
    """Rapport sans sonde (pour la re-decision apres une 1ere manoeuvre)."""
    s = enemy_stats(env)
    if s is None or s["n"] == 0:
        return (note + " " if note else "") + "L'ennemi n'a plus de presence notable."
    desc = "L'ennemi n'est PAS sur l'objectif" if s["in_obj"] == 0 else "L'ennemi tient l'objectif (%d unites)" % s["in_obj"]
    if s["out60"] == 0 and s["disp"] < 45:
        desc += ", masse en perimetre dense, aucun ecran dehors"
    return (note + " " if note else "") + desc + "."


def decide_maneuver(report):
    try:
        dec = officer_op.decide(report)
    except Exception as e:
        return {"manoeuvre": "M3", "posture": "?", "justification": "officier indisponible (%s)" % type(e).__name__}
    return dec


def norm_man(dec):
    man = str(dec.get("manoeuvre", "M3")).upper().replace(" ", "")[:3].rstrip("-")
    return man if man in M.MANEUVERS else "M3"


def run_officer_op(srv, seed, enemy, verbose=False, max_wall=1200, stall_wall=500):
    orders = []
    def order(t):
        orders.append(t)
        if verbose:
            print("   [OFFICIER] " + t, flush=True)
    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env, garrison, prof = setup_op(srv, seed, enemy)

    rep, _s0, _s1 = probe(env, brain)
    order("RAPPORT : " + rep)
    dec = decide_maneuver(rep); man = norm_man(dec)
    order("DECISION : posture=%s -> %s | %s" % (dec.get("posture", "?"), man, dec.get("justification", "")))

    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = garrison[0][2]
    r = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
    r.run(max_steps=500, max_wall=max_wall, stall_wall=stall_wall)
    m = metrics_dyn(env, r, garrison)

    redecision = None
    if not m["mil"] and m["pertes"] < 0.6 and env.en_alive().any():
        rep2 = static_report(env, "Apres une tentative en %s (objectif non pris, pertes %d%%) :" % (man, int(100 * m["pertes"])))
        order("DEGRADE -> " + rep2)
        dec2 = decide_maneuver(rep2); man2 = norm_man(dec2)
        if man2 != man:
            order("RE-DECISION : bascule %s -- %s" % (man2, dec2.get("justification", "")))
            plan2 = M.MANEUVERS[man2](qrf="inf"); plan2["garr_n"] = garrison[0][2]
            r2 = OperationRunner(env, brain, plan2, log_path="/dev/null", verbose=False)
            r2.run(max_steps=300, max_wall=max_wall, stall_wall=stall_wall)
            m = metrics_dyn(env, r2, garrison); redecision = man2
    m["manoeuvre"] = man; m["redecision"] = redecision; m["posture_estimee"] = dec.get("posture", "?")
    m["orders"] = orders
    return m


def recon_only(srv, seed, enemy):
    """1.1-bis : SONDE + DECISION seulement (pas d'execution) -> pour tester la reconnaissance vite."""
    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env, garrison, prof = setup_op(srv, seed, enemy)
    rep, s0, s1 = probe(env, brain)
    dec = decide_maneuver(rep)
    return rep, dec.get("posture", "?"), norm_man(dec), s0, s1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true"); p.add_argument("--recon", action="store_true")
    p.add_argument("--enemy", type=str, default="skilled_appat")
    p.add_argument("--srv", type=int, default=0); p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()
    if a.recon:
        rep, post, man, _s0, _s1 = recon_only(a.srv, a.seed, a.enemy)
        print("ennemi reel=%s | RAPPORT: %s | -> posture estimee=%s manoeuvre=%s" % (a.enemy, rep, post, man))
    elif a.smoke:
        print("=== SMOKE officier-live : ennemi=%s ===" % a.enemy, flush=True)
        m = run_officer_op(a.srv, a.seed, a.enemy, verbose=True)
        print("\n[RESULTAT] manoeuvre=%s redecision=%s mil=%s pertes=%d%% posture=%s"
              % (m["manoeuvre"], m["redecision"], m["mil"], int(100 * m["pertes"]), m["posture_estimee"]), flush=True)
