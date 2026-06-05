import numpy as np
from arma_env_koth import ArmaEnvKoth
M = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge0.Altis"
L = "/mnt/data/harmattan-sandbox/logs/server0.out"
env = ArmaEnvKoth(num_envs=2, mission=M, log=L, max_steps=40, seed=1)
obs = env.reset()
print("RESET obs/camp:", [o.shape for o in obs], "obj0=", (int(env.objx[0]), int(env.objy[0])))
print("vivants par camp:", [env._alive(c).sum(1).tolist() for c in range(3)])
for t in range(3):
    a = [np.random.randint(0, 4, (2, 3)) for _ in range(3)]
    obs, rew, done, info = env.step(*a)
    al = [int(env._alive(c).sum()) for c in range(3)]
    print("STEP", t, "| vivants BLU/OPF/IND=%d/%d/%d" % tuple(al),
          "| cap_prog", env.cap_prog.tolist(), "owner", env.cap_owner.tolist(),
          "| winner", info["winner"].tolist(), "| done", done.tolist())
print("OK C.1 — 3 factions tournent dans le vrai Arma")
