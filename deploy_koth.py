"""C.2 — déploiement temps réel du cerveau league_learner sur les 3 factions, avec calibration de tempo (move)."""
import numpy as np, torch
from arma_env_koth import ArmaEnvKoth
from train_koth_gpu import Net
M = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge0.Altis"
L = "/mnt/data/harmattan-sandbox/logs/server0.out"
dev = "cuda:0"
net = Net(10, 4, 512, 3).to(dev); net.load_state_dict(torch.load("/home/younes/arma3-marl/league_learner.pt", map_location=dev)); net.eval()
env = ArmaEnvKoth(num_envs=2, mission=M, log=L, max_steps=90, move=40, seed=5)
obs = env.reset(); hist = np.zeros(4, int); caps = 0
def act(o):
    with torch.no_grad():
        return torch.distributions.Categorical(logits=net.a_logits(torch.as_tensor(o, dtype=torch.float32, device=dev))).sample().cpu().numpy()
for t in range(26):
    a = [act(obs[c]) for c in range(3)]
    for x in a:
        for v in x.reshape(-1): hist[v] += 1
    obs, rew, done, info = env.step(*a)
    inz = []
    for c in range(3):
        d2 = (env.px[c] - env.objx[:, None]) ** 2 + (env.py[c] - env.objy[:, None]) ** 2
        inz.append(int(((d2 <= env.secure_r ** 2) & env._alive(c)).sum()))
    caps += int(info["captured"].sum())
    if t % 3 == 0 or info["captured"].any():
        print("t%02d | zone BLU/OPF/IND=%d/%d/%d | cap_prog %s | winner %s | caps %d"
              % (t, inz[0], inz[1], inz[2], [round(x,1) for x in env.cap_prog.tolist()], info["winner"].tolist(), caps))
print("actions HOLD/AVANCER/SUPPR/COUVERT =", hist.tolist(), "| captures totales:", caps)
