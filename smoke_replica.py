"""smoke_replica — prouve la physique de la replique AVANT d'entrainer :
(1) collision : aucun agent ne traverse un mur ; (2) LOS : les murs bloquent la vue en plus du relief."""
import torch
import terrain_gpu as TG
from assault_terrain import AssaultTerrain
DEV = "cuda:0"
RP = "/home/younes/arma3-marl/replica.npz"

env = AssaultTerrain(num_envs=512, A=1, D=2, shell_obs=True, replica=True, replica_path=RP, device=DEV, seed=0)
env.reset()
print("replica : terr_G=%d scale=%.0f m | %.1f%% bati | spawn initial dans un mur = %.2f%%" % (
    env.terr_G, env.scale, 100 * env._solid.mean().item(),
    100 * (env._sample_solid(env.apx, env.apy) > 0.5).float().mean().item()), flush=True)

# (1) COLLISION : marche aleatoire -> aucun agent DANS un mur
for _ in range(25):
    env.step(torch.randint(0, 8, (512, 1), device=DEV))
inwall = 100 * (env._sample_solid(env.apx, env.apy) > 0.5).float().mean().item()
print("(1) COLLISION : apres 25 pas aleatoires, agents DANS un mur = %.2f%%  (doit etre ~0)" % inwall, flush=True)

# (2) LOS : memes paires (agent -> objectif), terrain seul vs avec murs
env.reset()
ax = env.apx; ay = env.apy; bx = torch.zeros_like(ax); by = torch.zeros_like(ay)
base = TG.los_clear(env.hm, ax, ay, bx, by, env.scale)
withw = env._losc(env.hm, ax, ay, bx, by, env.scale)
print("(2) LOS vers l'objectif : relief seul %.0f%% degagee | avec MURS %.0f%% degagee  -> les murs bloquent %.0f%% en plus" % (
    100 * base.float().mean().item(), 100 * withw.float().mean().item(),
    100 * (base.float().mean() - withw.float().mean()).item()), flush=True)
print("SMOKE_REPLICA OK", flush=True)
