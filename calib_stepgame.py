"""calib_stepgame — mesure le rythme temps-de-jeu/pas de l ANCIEN harnais sur flotte SAINE.
Joue 1 op M1-vs-skilled (cadence ancienne, serveur 0) en encadrant run() par des lectures du
temps de simulation -> step_game = (g1-g0)/steps. C est LA constante qui preserve la dynamique
historique une fois la cadence passee en temps de jeu."""
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
from enemy_profiles import apply_profile, PRO_SKILL_SQF
from geometries import GEOMETRIES
import maneuvers as M

SB = "/mnt/data/harmattan-sandbox"
brain = Net(10, 4, 512, 3).to("cuda:0")
brain.load_state_dict(torch.load("koth_finetuned.pt", map_location="cuda:0")); brain.eval()
plan = M.MANEUVERS["M1"](qrf="inf")
env = OpArma(squads=M.SQUADS, mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", move=36, seed=77)
garrison, prof = apply_profile(env, "skilled", GEOMETRIES["standard"])
plan["garr_n"] = garrison[0][2]
env.spawn(M.SPAWNS, garrison)
env.b.send(PRO_SKILL_SQF, wait=True)
import time as _t
# 0) rythme du temps de jeu au repos (verite sur setAccTime : dedie = x1 attendu)
r0 = env._game_time(); _t.sleep(8.0); r1 = env._game_time()
rate = (r1 - r0) / 8.0 if (r0 > 0 and r1 > 0) else -1
print("RATE: temps de jeu / temps mur au repos = %.2f (setAccTime %s)" % (rate, "ACTIF" if rate > 1.5 else "INERTE (dedie)"))
g0 = env._game_time()
assert g0 > 0, "CALIB ECHEC : lecture du temps de jeu impossible (g0=%.1f)" % g0
runner = OperationRunner(env, brain, plan, log_path="/dev/null", verbose=False)
runner.run(max_steps=60, max_wall=600, stall_wall=400)
g1 = env._game_time()
steps = runner.step_i
assert g1 > g0, "CALIB ECHEC : g1 <= g0"
sg = (g1 - g0) / max(1, steps)
print("CALIB: g0=%.1f g1=%.1f steps=%d -> step_game = %.2f s-jeu/pas" % (g0, g1, steps, sg))
assert 0.5 < sg < 30, "CALIB ECHEC : step_game hors bande plausible [0.5, 30] : %.2f" % sg
open("/tmp/hmt_step_game.txt", "w").write("%.2f" % sg)
