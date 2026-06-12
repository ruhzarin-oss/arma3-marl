"""officer_live — JALON 1.3/1.4/1.5 : operation COMMANDEE PAR L'OFFICIER en live dans Arma.
Flux : SONDE (probe) -> lit la disposition ennemie -> RAPPORT DE CONTACT -> l'officier (qwen) DECIDE la
manoeuvre -> execute via OperationRunner -> si ca echoue, RE-DECIDE et change de manoeuvre (adaptation).
Journal d'ordres en clair (1.4 observabilite). Mesure (1.5) : officier adaptatif vs M3-fixe, posture ALEATOIRE/op."""
import time, json, argparse, random
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


def enemy_sectors(env):
    """Ennemis VIVANTS repartis en secteurs autour de l'objectif (pour le rapport de contact)."""
    al = env.en_alive()
    if env.en_n == 0 or not al.any():
        return {}, 0
    gx, gy = env.base
    ex, ey = env.epx[al], env.epy[al]
    sect = {"dans_objectif": 0, "nord": 0, "sud": 0, "est": 0, "ouest": 0}
    for x, y in zip(ex - gx, ey - gy):
        if abs(x) < 30 and abs(y) < 30:
            sect["dans_objectif"] += 1
        elif abs(y) >= abs(x):
            sect["nord" if y > 0 else "sud"] += 1
        else:
            sect["est" if x > 0 else "ouest"] += 1
    return sect, int(al.sum())


def build_report(env, probe_note=""):
    sect, n = enemy_sectors(env)
    inobj = sect.get("dans_objectif", 0)
    rep = ", ".join("%s:%d" % (k, v) for k, v in sect.items() if v > 0) or "aucun contact"
    L = ["Objectif : %s." % ("occupe par l'ennemi (%d unites)" % inobj if inobj > 0 else "ennemi NON present sur l'objectif"),
         "Disposition ennemie par secteur (relatif a l'objectif) : %s (%d visibles)." % (rep, n)]
    if probe_note:
        L.append(probe_note)
    return " ".join(L)


def setup_op(srv, seed, enemy, log_orders):
    """Prepare l'op : env + garnison + profil ennemi. Renvoie (env, brain, garrison)."""
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


def probe(env, brain, steps=10):
    """Sonde : avance APPUI + ASSAUT vers l'objectif pour declencher la reaction ennemie, puis lit."""
    before, _ = enemy_sectors(env)
    for sq in env.squads:
        si = env.squads.index(sq)
        env.goals[si] = np.array(M.COMPLEXE if "ASSAUT" in sq else M.CRETE, dtype=float)
        env.stances[si] = "move"
    for _ in range(steps):
        with torch.no_grad():
            acts = [_act(env, brain, si) for si in range(env.S)]
        env.step(acts)
    after, _ = enemy_sectors(env)
    # note de sonde : l'ennemi a-t-il bouge/reagi ?
    note = ""
    if not after:
        note = "Au contact, l'ennemi a quitte ses positions (objectif vide)."
    return note


def _act(env, brain, si):
    o = torch.as_tensor(env.obs(si), dtype=torch.float32, device=DEV)
    with torch.no_grad():
        lg = brain.a_logits(o) + torch.as_tensor(STANCES[env.stances[si]], device=DEV)
    return torch.distributions.Categorical(logits=lg).sample().cpu().numpy()


def run_officer_op(srv, seed, enemy, verbose=False, max_wall=1200, stall_wall=500):
    """Une operation COMMANDEE PAR L'OFFICIER (sonde -> decision -> execution -> re-decision)."""
    orders = []
    def order(txt):
        orders.append(txt)
        if verbose:
            print("   [OFFICIER] " + txt, flush=True)
    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env, garrison, prof = setup_op(srv, seed, enemy, order)

    note = probe(env, brain, steps=10)
    rep = build_report(env, note)
    order("RAPPORT DE CONTACT recu : " + rep)
    try:
        dec = officer_op.decide(rep)
    except Exception as e:
        dec = {"manoeuvre": "M3", "posture": "?", "justification": "officier indisponible (%s) -> defaut M3" % type(e).__name__}
    man = str(dec.get("manoeuvre", "M3")).upper().replace(" ", "")[:3].rstrip("-")
    if man not in M.MANEUVERS:
        man = "M3"
    order("DECISION : posture estimee = %s -> manoeuvre %s" % (dec.get("posture", "?"), man))
    order("JUSTIFICATION : " + str(dec.get("justification", "")))
    order("ALLOCATION : " + str(dec.get("allocation", "")))

    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = garrison[0][2]
    runner = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
    runner.run(max_steps=500, max_wall=max_wall, stall_wall=stall_wall)
    m = metrics_dyn(env, runner, garrison)

    # RE-DECISION (1.3) : si l'op a echoue et qu'il reste du monde, l'officier change de manoeuvre
    redecision = None
    if not m["mil"] and m["pertes"] < 0.6 and env.en_alive().any():
        rep2 = build_report(env, "Apres une premiere tentative en %s : objectif non pris, pertes %d%%." % (man, int(100 * m["pertes"])))
        order("SITUATION DEGRADEE -> nouvelle lecture : " + rep2)
        try:
            dec2 = officer_op.decide(rep2)
            man2 = str(dec2.get("manoeuvre", "M1")).upper().replace(" ", "")[:3].rstrip("-")
            if man2 in M.MANEUVERS and man2 != man:
                order("RE-DECISION : bascule en %s -- %s" % (man2, dec2.get("justification", "")))
                plan2 = M.MANEUVERS[man2](qrf="inf"); plan2["garr_n"] = garrison[0][2]
                r2 = OperationRunner(env, brain, plan2, log_path="/dev/null", verbose=False)
                r2.run(max_steps=300, max_wall=max_wall, stall_wall=stall_wall)
                m = metrics_dyn(env, r2, garrison)
                redecision = man2
        except Exception:
            pass
    m["manoeuvre"] = man; m["redecision"] = redecision; m["posture_estimee"] = dec.get("posture", "?")
    m["orders"] = orders
    return m


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--enemy", type=str, default="skilled_appat")
    p.add_argument("--srv", type=int, default=0); p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()
    if a.smoke:
        print("=== SMOKE officier-live : ennemi=%s (l'officier ne le sait PAS, il doit le deduire) ===" % a.enemy, flush=True)
        m = run_officer_op(a.srv, a.seed, a.enemy, verbose=True)
        print("\n[RESULTAT] manoeuvre=%s redecision=%s | mil=%s pertes=%d%% garr_pris=%s posture_estimee=%s"
              % (m["manoeuvre"], m["redecision"], m["mil"], int(100 * m["pertes"]), m["garr_pris"], m["posture_estimee"]), flush=True)
