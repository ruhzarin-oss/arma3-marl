"""ÉTAPE C.4 — ARÈNE LIVE. Le cerveau affiné (koth_finetuned.pt) pilote 3 factions dans une bataille KotH continue
sur le serveur 0, en boucle infinie (auto-reset). Quand un HUMAIN se connecte, il est téléporté sur la colline,
côté BLUFOR (allié de la faction BLU, hostile à OPF/IND). Younes joue comme 4e acteur. Ctrl-C / pkill pour arrêter."""
import time, numpy as np, torch
from arma_env_koth import ArmaEnvKoth
from train_koth_gpu import Net
M = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge0.Altis"
L = "/mnt/data/harmattan-sandbox/logs/server0.out"
dev = "cuda:0"
net = Net(10, 4, 512, 3).to(dev)
net.load_state_dict(torch.load("/home/younes/arma3-marl/koth_finetuned.pt", map_location=dev)); net.eval()
env = ArmaEnvKoth(num_envs=1, mission=M, log=L, move=36, max_steps=120, seed=7)
obs = env.reset()
print("ARENE LIVE prete — serveur 0 (100.66.136.67:2402), cerveau koth_finetuned.pt. Connecte-toi en BLUFOR.", flush=True)
def act(o):
    with torch.no_grad():
        return torch.distributions.Categorical(logits=net.a_logits(torch.as_tensor(o, dtype=torch.float32, device=dev))).sample().cpu().numpy()
i = 0; caps = 0
while True:
    a = [act(obs[c]) for c in range(3)]
    obs, rew, done, info = env.step(*a)
    caps += int(info["captured"].sum()); i += 1
    ox, oy = int(env.objx[0]), int(env.objy[0])
    # teleporter un joueur humain sur la colline (cote BLU, ~130m au nord) s'il est loin
    if i % 2 == 0:
        env.b.send('{ if (isPlayer _x && {(_x distance2D [%d,%d]) > 700}) then { _x setPosATL [%d,%d,0]; _x setDir 180; }; } forEach allUnits;' % (ox, oy, ox, oy + 130), wait=True)
    if i % 5 == 0:
        inz = [int(((((env.px[c]-env.objx[:,None])**2+(env.py[c]-env.objy[:,None])**2) <= env.secure_r**2) & env._alive(c)).sum()) for c in range(3)]
        print("boucle %d | colline=(%d,%d) | dans zone BLU/OPF/IND=%d/%d/%d | captures %d | %s" % (i, ox, oy, inz[0], inz[1], inz[2], caps, time.strftime("%H:%M:%S")), flush=True)
