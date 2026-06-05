import numpy as np
from arma_env_koth import ArmaEnvKoth
M = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge0.Altis"
L = "/mnt/data/harmattan-sandbox/logs/server0.out"
env = ArmaEnvKoth(num_envs=2, mission=M, log=L, max_steps=80, seed=3)
env.reset()
print("obj0=", int(env.objx[0]), int(env.objy[0]), "| dist moyenne initiale par camp:", [round(float(env._mean_dist(c)[0]), 2) for c in range(3)])
for t in range(8):
    a = [np.ones((2, 3), int) for _ in range(3)]  # tout le monde AVANCER
    env.step(*a)
    md = [round(float(env._mean_dist(c)[0]), 2) for c in range(3)]
    inz = []
    for c in range(3):
        d2 = (env.px[c] - env.objx[:, None]) ** 2 + (env.py[c] - env.objy[:, None]) ** 2
        inz.append(int(((d2 <= env.secure_r ** 2) & env._alive(c))[0].sum()))
    print("t%d | dist(colline) BLU/OPF/IND=%s | dans zone (env0)=%s | pos BLU0=%d,%d" % (t, md, inz, int(env.px[0][0,0]), int(env.py[0][0,0])))
