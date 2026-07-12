"""run_paros — execute une manoeuvre du repertoire sur le THEATRE PAROS (ville de colline) dans le vrai Arma.
Auto-suffisant : utilise paros.SQUADS/SPAWNS/GARRISON (garnison urbaine). Smoke = 1 op verbeuse pour valider
que le theatre est combat-viable avant de l'instrumenter / le visualiser."""
import time, argparse
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"


def run_one(brain, maneuver, srv, seed, verbose, max_steps, max_wall, stall_wall):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=M.SQUADS, mission=mis, log=log, move=36, seed=seed)
    plan = M.MANEUVERS[maneuver](qrf="inf")
    plan["garr_n"] = M.GARRISON[0][2]
    env.spawn(M.SPAWNS, M.GARRISON)
    runner = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=verbose)
    ok = runner.run(max_steps=max_steps, max_wall=max_wall, stall_wall=stall_wall)
    eal = env.en_alive(); en_tot = env.en_n
    garr_killed = 1.0 - (float(eal.sum()) / en_tot if en_tot else 0.0)
    alive = sum(int(env.alive(si).sum()) for si in range(env.S))
    losses = 1.0 - alive / sum(env.sizes)
    return {"succes": bool(ok), "garr_killed": garr_killed, "losses": losses, "abort": getattr(runner, "abort_reason", None)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--maneuver", type=str, default="M3"); p.add_argument("--srv", type=int, default=1); p.add_argument("--seed", type=int, default=1)
    p.add_argument("--max_steps", type=int, default=400); p.add_argument("--max_wall", type=float, default=600); p.add_argument("--stall_wall", type=float, default=300)
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    print("=== SMOKE PAROS — %s sur le theatre ville-de-colline (objectif %s) ===" % (a.maneuver, M.COMPLEXE), flush=True)
    m = run_one(brain, a.maneuver, a.srv, a.seed, True, a.max_steps, a.max_wall, a.stall_wall)
    print("\n>>> PAROS %s : succes=%s | garnison neutralisee %.0f%% | pertes %.0f%% | abort=%s"
          % (a.maneuver, m["succes"], 100 * m["garr_killed"], 100 * m["losses"], m["abort"]), flush=True)
    print("PAROS SMOKE FINI", flush=True)
