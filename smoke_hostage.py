import torch, math, sys
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
DEV = "cuda:0"

env = HostageEnv(num_envs=2048, A=9, D=6, device=DEV, seed=0)
print("obs_dim", env.obs_dim, "n_actions", env.n_actions, "A", env.A, "D", env.D, flush=True)
obs = env.reset()
print("obs shape", tuple(obs.shape), flush=True)
succ = hd = sw = to = nep = 0
maxpick = 0.0
for t in range(500):
    ax, ay = env.B.apx, env.B.apy
    px = torch.where(env.picked[:, None] > 0.5, env.extx[:, None], env.hpx[:, None])
    py = torch.where(env.picked[:, None] > 0.5, env.exty[:, None], env.hpy[:, None])
    dx = px - ax; dy = py - ay
    act = (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)) % 8).long()
    obs, rew, done, info = env.step(act)
    maxpick = max(maxpick, env.picked.mean().item())
    dm = done.bool()
    if dm.any():
        succ += info["success"][dm].float().sum().item()
        hd += info["hdead"][dm].float().sum().item()
        sw += info["squad_wipe"][dm].float().sum().item()
        nep += int(dm.sum())
print("=== SMOKE escouade scriptee (fonce + exfil, sans tactique) ===", flush=True)
print("episodes %d | succes %.0f%% | otage mort %.0f%% | escouade aneantie %.0f%% | pickup max %.0f%%"
      % (nep, 100 * succ / max(nep, 1), 100 * hd / max(nep, 1), 100 * sw / max(nep, 1), 100 * maxpick), flush=True)
print("SMOKE FINI", flush=True)
