"""Video FURTIVITE top-down : on DESSINE les cones de vue des gardes (rouge) -> on VOIT l'agent
se faufiler entre eux jusqu'a l'objectif (vert), sans entrer dans le rouge. agent bleu / jaune si vu."""
import sys, math, torch, numpy as np
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from stealth_env import StealthEnv
from train_koth_gpu import Net
import imageio.v2 as imageio
DEV = "cpu"; D = 4
net = Net(23, 10, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/stealth_d%d.pt" % D, map_location=DEV)); net.eval()


def run():
    best = None
    for seed in range(250):
        env = StealthEnv(num_envs=1, A=1, D=D, device=DEV, seed=seed); obs = env.reset()
        S = env.S; gx = env.B.dpx[0].tolist(); gy = env.B.dpy[0].tolist(); gf = env.gface[0].tolist()
        path = []
        for t in range(150):
            det, _, _, _, _ = env._detect()
            path.append((float(env.B.apx[0, 0]), float(env.B.apy[0, 0]), bool(det[0, 0])))
            with torch.no_grad(): a = net.a_logits(obs).argmax(-1)
            obs, rw, done, info = env.step(a)
            if bool(done[0]):
                path.append((float(env.B.apx[0, 0]), float(env.B.apy[0, 0]), bool(env._detect()[0][0, 0])))
                if bool(info["success"][0]) and (best is None or len(path) > len(best[0])):
                    best = (path, gx, gy, gf, S, env.fov, env.drange)
                break
        if best is not None and len(best[0]) >= 30: break        # un beau zigzag suffit
    return best


path, gx, gy, gf, S, fov, drange = run()
print("infiltration : %d frames, succes=%s" % (len(path), str(len(path) > 0)), flush=True)
R = np.load("/home/younes/arma3-marl/replica.npz"); solid = R["solid"]; GS = solid.shape[0]


def w2p(x, y):
    return min(max(int(((x / S) * 0.5 + 0.5) * (GS - 1)), 0), GS - 1), min(max(int(((y / S) * 0.5 + 0.5) * (GS - 1)), 0), GS - 1)


# fond statique : solide gris + TINT ROUGE dans les cones de vue
bg = np.full((GS, GS, 3), 245, dtype=np.uint8); bg[solid > 0.5] = [120, 120, 120]
for r in range(GS):
    for c in range(GS):
        wx = (c / (GS - 1) * 2 - 1) * S; wy = (r / (GS - 1) * 2 - 1) * S
        for j in range(D):
            dx = wx - gx[j]; dy = wy - gy[j]; dist = math.hypot(dx, dy)
            if dist < drange and dist > 1:
                off = abs((math.atan2(dy, dx) - gf[j] + math.pi) % (2 * math.pi) - math.pi)
                if off < fov:
                    bg[r, c] = [min(255, int(bg[r, c, 0]) + 0), 200, 200] if False else [255, int(bg[r, c, 1] * 0.6), int(bg[r, c, 2] * 0.6)]
                    break
for j in range(D):
    c, r = w2p(gx[j], gy[j])
    for dx in range(-1, 2):
        for dy in range(-1, 2): bg[min(max(r + dy, 0), GS - 1), min(max(c + dx, 0), GS - 1)] = [150, 0, 0]
oc, orr = w2p(0.0, 0.0)
for dx in range(-2, 3):
    for dy in range(-2, 3): bg[min(max(orr + dy, 0), GS - 1), min(max(oc + dx, 0), GS - 1)] = [30, 200, 30]

frames = []
for (ax, ay, det) in path:
    img = bg.copy(); c, r = w2p(ax, ay); col = [255, 230, 0] if det else [40, 90, 235]
    for dx in range(-1, 2):
        for dy in range(-1, 2): img[min(max(r + dy, 0), GS - 1), min(max(c + dx, 0), GS - 1)] = col
    frames.append(np.repeat(np.repeat(img, 6, 0), 6, 1))
imageio.mimwrite("/home/younes/compose-embodiment/stealth_infil.mp4", frames, fps=5, macro_block_size=1)
print("VIDEO -> stealth_infil.mp4 (%d frames) | rouge=cones de vue, bleu=agent furtif (jaune=vu), vert=objectif" % len(frames), flush=True)
