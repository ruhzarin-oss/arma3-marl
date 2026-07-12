"""run_paros_staff — op PAROS pilotee par l'OFFICIER-LLM, qui alimente le dashboard etat-major en temps reel
(staff/state.json a chaque pas). Tourne sur un serveur de mesure (fiable). Le LLM lit -> choisit -> ca s'execute
-> tu regardes la carte etat-major dans le navigateur."""
import time, json, os, argparse
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
import paros as M
import officer_op
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"; STAFF = "/home/younes/arma3-marl/staff/state.json"
COL = {"SQ_APPUI": "#3b82f6", "SQ_A_OUEST": "#22c55e", "SQ_A_EST": "#f59e0b", "SQ_RESERVE": "#eab308"}
LLM = {}

REPORT = ("Objectif TENU. Garnison urbaine d'environ 12 hommes massee dans la ville de Paros (bati dense), "
          "ecran de patrouilles ~8 hommes au nord. Pas de reserve mobile. Terrain : crete d'appui au nord-ouest "
          "qui domine la ville, flancs ouest et est praticables, approche qui monte depuis le sud.")


def dump(runner):
    env = runner.env
    sq = {}
    for si, nm in enumerate(env.squads):
        units = [[int(env.px[si][u]), int(env.py[si][u]), int(env.dmg[si][u] < env.dmg_dead * 100)] for u in range(env.sizes[si])]
        sq[nm] = {"color": COL.get(nm, "#ddd"), "units": units, "goal": [int(env.goals[si][0]), int(env.goals[si][1])], "stance": env.stances[si]}
    en = [[int(env.epx[k]), int(env.epy[k]), int(env.edmg[k] < env.dmg_dead * 100)] for k in range(env.en_n)]
    st = {"op": runner.opname, "step": runner.step_i, "losses": round(runner.losses(), 3), "squads": sq, "enemies": en,
          "pts": {"COMPLEXE": list(M.COMPLEXE), "CRETE": list(M.CRETE), "FLANC_O": list(M.FLANC_O), "FLANC_E": list(M.FLANC_E), "QRF": list(M.QRF_PT)},
          "llm": LLM}
    try:
        json.dump(st, open(STAFF, "w"))
    except Exception:
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--srv", type=int, default=2); p.add_argument("--seed", type=int, default=5)
    p.add_argument("--max_steps", type=int, default=400); p.add_argument("--acc", type=float, default=4.0)
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    print("=== OFFICIER-LLM lit la situation de Paros... ===", flush=True)
    d = officer_op.decide(REPORT)
    raw = str(d.get("manoeuvre", "M3")).upper(); man = next((mk for mk in M.MANEUVERS if mk in raw), "M3")
    LLM.update({"posture": d.get("posture"), "maneuver": man, "justification": d.get("justification"), "allocation": d.get("allocation")})
    print("[LLM] posture: %s\n[LLM] manoeuvre: %s\n[LLM] justification: %s" % (d.get("posture"), man, d.get("justification")), flush=True)
    env = OpArma(squads=M.SQUADS, mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % a.srv, log=SB + "/logs/server%d.out" % a.srv, move=36, acc=a.acc, seed=a.seed)
    plan = M.MANEUVERS[man](qrf="inf"); plan["garr_n"] = M.GARRISON[0][2]
    env.spawn(M.SPAWNS, M.GARRISON)
    runner = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=True)
    runner.opname = "PAROS / OFFICIER-LLM / " + man
    dump(runner)
    ok = runner.run(max_steps=a.max_steps, max_wall=700, stall_wall=300, trace=dump)
    dump(runner)
    eal = env.en_alive()
    print("\n>>> %s | objectif %s | garnison neutralisee %.0f%% | pertes %.0f%%"
          % (man, "PRIS" if ok else "non pris", 100 * (1 - eal.mean()), 100 * runner.losses()), flush=True)
    print("PAROS STAFF FINI", flush=True)
