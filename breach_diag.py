import sys, math, torch
sys.path.insert(0, "/home/younes/compose-embodiment"); sys.path.insert(0, "/home/younes/arma3-marl")
from breach_env import BreachEnv
DEV = "cuda:0"
# agent spawn 8 m PILE dans le dos (jit=0) -> deja en position de takedown des le 1er pas
env = BreachEnv(num_envs=256, A=1, D=1, device=DEV, seed=1, spawn_r=8.0, spawn_jit_deg=0.0)
obs = env.reset()
_, td, toff, tb, tal = env._tgt()
print("INIT  dist=%.1f  off=%.0fdeg  behind=%.2f  alive=%.2f" % (td.mean(), math.degrees(toff.mean()), tb.mean(), tal.mean()), flush=True)
print("td_range=%.1f  td_arc=%.0fdeg" % (env.td_range, math.degrees(env.td_arc)), flush=True)
det, _, _, _, _ = env._detect(); print("detecte au spawn: %.0f%%" % (100 * det.float().mean()), flush=True)
tot_succ = 0; nep = 0
for t in range(6):
    a = torch.full((256, 1), 8, dtype=torch.long, device=DEV)   # HOLD : reste en position
    obs, rw, done, info = env.step(a)
    k = info["killed"].float().mean().item(); s = info["success"].float().mean().item()
    print("  pas %d : killed=%.0f%%  success=%.0f%%  rew_moy=%.2f" % (t, 100 * k, 100 * s, rw.mean().item()), flush=True)
print("=> si killed/success ~100%% le mecanisme MARCHE (probleme = apprentissage de l'approche)", flush=True)
