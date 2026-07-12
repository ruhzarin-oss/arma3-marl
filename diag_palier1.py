"""diag_palier1 — pourquoi le palier 1 (point-blank 20v2) fait 0% ? On verifie : defenseurs dans des murs ?
LOS bloquee a bout portant ? distance reelle ?"""
import torch
import terrain_gpu as TG
from assault_terrain import AssaultTerrain
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
env = AssaultTerrain(num_envs=256, A=20, D=2, R_spawn=30.0, relief=40.0, hit=0.10,
                     shell_obs=True, team_obs=True, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
env.reset()
dw = (env._sample_solid(env.dpx, env.dpy) > 0.5).float().mean().item()
aw = (env._sample_solid(env.apx, env.apy) > 0.5).float().mean().item()
ex = env.dpx.unsqueeze(1) - env.apx.unsqueeze(2); ey = env.dpy.unsqueeze(1) - env.apy.unsqueeze(2)
d2 = ex * ex + ey * ey; km = d2.argmin(2)
bx = torch.gather(env.dpx, 1, km); by = torch.gather(env.dpy, 1, km)
dist = torch.sqrt((env.apx - bx) ** 2 + (env.apy - by) ** 2)
los = env._losc(env.hm, env.apx, env.apy, bx, by, env.scale)
losT = TG.los_clear(env.hm, env.apx, env.apy, bx, by, env.scale)
print("=== DIAG PALIER 1 (A=20 vs D=2, depart 30 m) ===", flush=True)
print(" defenseurs DANS un mur          : %.0f%%  (s'ils sont dans un mur -> intouchables)" % (100 * dw), flush=True)
print(" attaquants dans un mur (post-nudge): %.0f%%" % (100 * aw), flush=True)
print(" distance attaquant->defenseur     : moy %.0f m (min %.0f)" % (dist.mean().item(), dist.min().item()), flush=True)
print(" LOS attaquant->defenseur (relief+MURS) : %.0f%% degagee" % (100 * los.mean().item()), flush=True)
print(" LOS sans les murs (relief seul)        : %.0f%% degagee" % (100 * losT.mean().item()), flush=True)
print("DIAG FINI", flush=True)
