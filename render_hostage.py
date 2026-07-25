import sys, torch, numpy as np
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
import imageio.v2 as imageio
DEV = "cuda:0"

# net charge une fois (obs_dim fixe)
probe = HostageEnv(num_envs=1, A=9, D=3, device=DEV, seed=0)
O, NA = probe.obs_dim, probe.n_actions
net = Net(O, NA, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_squad.pt", map_location=DEV)); net.eval()
solid = probe.B._solid.cpu().numpy(); GS = solid.shape[0]; S = probe.B.scale


def put(img, x, y, color, r=1):
    cx = int((x / S * 0.5 + 0.5) * (GS - 1)); cy = int((y / S * 0.5 + 0.5) * (GS - 1))
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            rr = min(max(cy + dy, 0), GS - 1); cc = min(max(cx + dx, 0), GS - 1)
            img[rr, cc] = color


def frame(env):
    img = np.full((GS, GS, 3), 245, dtype=np.uint8)
    img[solid > 0.5] = [120, 120, 120]
    dal = env.B._dalive()[0].cpu().numpy(); dpx = env.B.dpx[0].cpu().numpy(); dpy = env.B.dpy[0].cpu().numpy()
    for j in range(env.D):
        put(img, dpx[j], dpy[j], [210, 40, 40] if dal[j] else [160, 160, 160], 1)
    put(img, float(env.extx[0]), float(env.exty[0]), [255, 160, 0], 2)
    put(img, float(env.hpx[0]), float(env.hpy[0]), [30, 200, 30], 2)
    ax = env.B.apx[0].cpu().numpy(); ay = env.B.apy[0].cpu().numpy()
    for i in range(env.A):
        put(img, ax[i], ay[i], [40, 90, 235], 1)
    return np.repeat(np.repeat(img, 8, 0), 8, 1)


chosen = None
for seed in range(30):
    env = HostageEnv(num_envs=1, A=9, D=3, device=DEV, seed=seed)
    obs = env.reset(); frames = []
    for t in range(160):
        with torch.no_grad():
            act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()   # echantillonne (regime du 80%)
        frames.append(frame(env))
        obs, rw, done, info = env.step(act)
        if bool(done[0]):
            ok = bool(info["success"][0]); frames.append(frame(env))
            print("seed %d : success=%d picked=%d wipe=%d t=%d" % (seed, ok, int(info["picked"][0]), int(info["squad_wipe"][0]), t), flush=True)
            if ok: chosen = frames
            break
    if chosen: break

if chosen is None: chosen = frames
imageio.mimwrite("/home/younes/compose-embodiment/hostage_rescue.mp4", chosen, fps=8, macro_block_size=1)
print("VIDEO %d frames -> hostage_rescue.mp4" % len(chosen), flush=True)
