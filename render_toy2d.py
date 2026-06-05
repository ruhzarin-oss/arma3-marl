import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
from toy2d import VectorizedToy2D

SEED = 7
rng = np.random.default_rng(SEED)
env = VectorizedToy2D(num_envs=1, seed=SEED)
env.reset()

def greedy(env):
    pos = env.pos[0]; c = env.obj_center
    acts = np.zeros(env.A, dtype=int)
    for i in range(env.A):
        if not env.alive[0, i]:
            acts[i] = 0; continue
        dr = c[0] - pos[i, 0]; dc = c[1] - pos[i, 1]
        if abs(dr) >= abs(dc) and abs(dr) > 0.5:
            acts[i] = 2 if dr > 0 else 1
        elif abs(dc) > 0.5:
            acts[i] = 4 if dc > 0 else 3
        else:
            acts[i] = 0
        if rng.random() < 0.15:
            acts[i] = int(rng.integers(0, 5))
    return acts.reshape(1, env.A)

frames = []
for _ in range(env.max_steps):
    frames.append((env.pos[0].copy(), env.alive[0].copy(), bool(env.success[0]), int(env.t[0])))
    if env.done[0]:
        break
    env.step(greedy(env), auto_reset=False)
frames.append((env.pos[0].copy(), env.alive[0].copy(), bool(env.success[0]), int(env.t[0])))

G = env.G
fig, ax = plt.subplots(figsize=(6, 6))
colors = ["#FFC300", "#1f77b4", "#2ca02c", "#9467bd"]
labels = ["C", "1", "2", "3"]

def draw(frame):
    pos, alive, success, step = frame
    ax.clear()
    ax.set_xlim(-0.5, G - 0.5); ax.set_ylim(G - 0.5, -0.5)
    ax.set_xticks(range(G)); ax.set_yticks(range(G))
    ax.grid(True, color="#dddddd", linewidth=0.5); ax.set_aspect("equal")
    lo = env.obj_lo; hi = env.obj_hi
    ax.add_patch(patches.Rectangle((lo[1]-0.5, lo[0]-0.5), hi[1]-lo[1]+1, hi[0]-lo[0]+1, color="#2ca02c", alpha=0.25))
    ax.text(env.obj_center[1], env.obj_center[0], "OBJ", ha="center", va="center", color="#1a7a1a", fontsize=9, fontweight="bold")
    for d in env.danger:
        ax.add_patch(patches.Rectangle((d[1]-0.5, d[0]-0.5), 1, 1, color="#d62728", alpha=0.35))
    for i in range(env.A):
        r, c = pos[i]
        if alive[i]:
            ax.scatter(c, r, s=340, color=colors[i], edgecolors="black", zorder=3)
            ax.text(c, r, labels[i], ha="center", va="center", fontsize=8, zorder=4)
        else:
            ax.scatter(c, r, s=200, color="#999999", marker="x", zorder=3)
    ndead = int((~alive).sum())
    t = f"Harmattan v0  -  pas {step}/{env.max_steps}  |  pertes: {ndead}/{env.A}"
    if success:
        t += "  |  OBJECTIF SECURISE"
    ax.set_title(t, fontsize=10)

anim = FuncAnimation(fig, draw, frames=frames, interval=300)
anim.save("episode.gif", writer=PillowWriter(fps=3))
print(f"GIF ecrit : episode.gif | {len(frames)} images | succes={frames[-1][2]} | pertes={int((~frames[-1][1]).sum())}/{env.A}")
