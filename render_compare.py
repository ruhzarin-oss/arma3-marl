"""Video COMPARATIVE cote a cote : GAUCHE = d6 (9 agents independants, eparpilles) /
DROITE = chef coordonne (axe commun + appui/assaut, soude). Meme env (D=6), top-down."""
import sys, torch, numpy as np
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
import imageio.v2 as imageio
DEV = "cpu"; S = 140.0


class Coord(nn.Module):
    def __init__(self, gdim, A, h=256):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(gdim, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.dirh = nn.Linear(h, 8); self.roleh = nn.Linear(h, A * 2); self.v = nn.Linear(h, 1); self.A = A

    def forward(self, o):
        z = self.tr(o); return self.dirh(z), self.roleh(z).view(-1, self.A, 2), self.v(z).squeeze(-1)


def gobs(env):
    N = env.N
    ag = torch.stack([env.B.apx / S, env.B.apy / S, env.B._aalive().float()], -1).reshape(N, -1)
    dg = torch.stack([env.B.dpx / S, env.B.dpy / S, env.B._dalive().float()], -1).reshape(N, -1)
    h = torch.stack([env.hpx / S, env.hpy / S, env.hdmg, env.picked], -1)
    e = torch.stack([env.extx / S, env.exty / S], -1)
    return torch.cat([ag, dg, h, e], -1)


d6 = Net(29, 10, 512, 3).to(DEV); d6.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); d6.eval()
probe = HostageEnv(num_envs=1, A=9, D=6, device=DEV, seed=0)
chef = Coord(gobs(probe).shape[-1], 9).to(DEV); chef.load_state_dict(torch.load("/home/younes/compose-embodiment/chef_coord.pt", map_location=DEV)); chef.eval()


def snap(env):
    return {"A": [(float(env.B.apx[0, i]), float(env.B.apy[0, i]), bool(env.B._aalive()[0, i])) for i in range(9)],
            "G": [(float(env.B.dpx[0, j]), float(env.B.dpy[0, j]), bool(env.B._dalive()[0, j])) for j in range(env.D)],
            "H": (float(env.hpx[0]), float(env.hpy[0]))}


def run(mode):
    for seed in range(60):
        env = HostageEnv(num_envs=1, A=9, D=6, device=DEV, seed=seed); env.ff_hit = 0.0; env.exfil_hit = 0.0
        obs = env.reset(); traj = []
        for t in range(170):
            traj.append(snap(env))
            with torch.no_grad():
                if mode == "d6":
                    act = torch.distributions.Categorical(logits=d6.a_logits(obs)).sample()
                else:
                    dl, rl, _ = chef(gobs(env)); d = torch.distributions.Categorical(logits=dl).sample(); r = torch.distributions.Categorical(logits=rl).sample()
                    act = torch.where(r == 1, d[:, None].expand(1, 9), torch.full((1, 9), 9, dtype=torch.long))
            obs, rw, done, info = env.step(act)
            if bool(done[0]):
                traj.append(snap(env))
                if bool(info["success"][0]): return traj, (float(env.extx[0]), float(env.exty[0]))
                break
    return traj, (float(env.extx[0]), float(env.exty[0]))


print("episode d6 (eparpille)...", flush=True); tj_d6, ext = run("d6")
print("episode chef (coordonne)...", flush=True); tj_ch, _ = run("chef")
print("d6 %d frames | chef %d frames" % (len(tj_d6), len(tj_ch)), flush=True)

R = np.load("/home/younes/arma3-marl/replica.npz"); solid = R["solid"]; GS = solid.shape[0]; GAP = 10


def pxy(x, y):
    return min(max(int(((x / S) * 0.5 + 0.5) * (GS - 1)), 0), GS - 1), min(max(int(((y / S) * 0.5 + 0.5) * (GS - 1)), 0), GS - 1)


def panel(fr):
    img = np.full((GS, GS, 3), 245, dtype=np.uint8); img[solid > 0.5] = [120, 120, 120]
    cx, cy = pxy(ext[0], ext[1])
    for dx in range(-2, 3):
        for dy in range(-2, 3): img[min(max(cy + dy, 0), GS - 1), min(max(cx + dx, 0), GS - 1)] = [255, 160, 0]
    for (gx, gy, al) in fr["G"]:
        c, r = pxy(gx, gy); img[r, c] = [210, 40, 40] if al else [165, 165, 165]
    hc, hr = pxy(fr["H"][0], fr["H"][1])
    for dx in range(-1, 2):
        for dy in range(-1, 2): img[min(max(hr + dy, 0), GS - 1), min(max(hc + dx, 0), GS - 1)] = [30, 200, 30]
    for (ax, ay, al) in fr["A"]:
        c, r = pxy(ax, ay); img[r, c] = [40, 90, 235] if al else [120, 120, 170]
    return img


T = max(len(tj_d6), len(tj_ch)); frames = []
for t in range(T):
    L = panel(tj_d6[min(t, len(tj_d6) - 1)]); Rr = panel(tj_ch[min(t, len(tj_ch) - 1)])
    canvas = np.full((GS, GS * 2 + GAP, 3), 255, dtype=np.uint8)
    canvas[:, :GS] = L; canvas[:, GS + GAP:] = Rr
    frames.append(np.repeat(np.repeat(canvas, 5, 0), 5, 1))
imageio.mimwrite("/home/younes/compose-embodiment/compare_squad.mp4", frames, fps=10, macro_block_size=1)
print("VIDEO -> compare_squad.mp4 (%d frames) | GAUCHE=d6 eparpille, DROITE=chef coordonne" % len(frames), flush=True)
