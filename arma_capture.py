import time
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
from arma_env import ArmaSquadEnv

env = ArmaSquadEnv(opfor=2)
obs = env.reset()
frames = [(list(env._squad), list(env._opfor), 0, 0)]
print("reset ok, capture en cours...")
for k in range(env.max_steps):
    acts = []
    for o in obs:
        dgx, dgy = o[2], o[3]
        acts.append((3 if dgx > 0 else 4) if abs(dgx) >= abs(dgy) else (1 if dgy > 0 else 2))
    obs, r, c, d, info = env.step(acts)
    frames.append((list(env._squad), list(env._opfor), info["in_obj"], info["alive"]))
    print("pas %d | dans_obj %d | vivants %d | done %s" % (k+1, info["in_obj"], info["alive"], d))
    if d: break

X0, Y0, S = env.x0, env.y0, env.size
fig, ax = plt.subplots(figsize=(6,6))
def draw(fr):
    squad, opf, in_obj, alive = fr; ax.clear()
    ax.set_xlim(X0-10, X0+S+10); ax.set_ylim(Y0-10, Y0+S+10); ax.set_aspect("equal"); ax.grid(True, color="#eee")
    ax.add_patch(patches.Circle((env.objx, env.objy), env.secure_r, color="#2ca02c", alpha=0.25))
    ax.text(env.objx, env.objy, "OBJ", ha="center", va="center", color="#1a7a1a", fontweight="bold")
    for u in opf:
        if u["alive"]: ax.scatter(u["x"], u["y"], s=240, color="#d62728", marker="s", edgecolors="black", zorder=3)
        else: ax.scatter(u["x"], u["y"], s=140, color="#999", marker="x", zorder=3)
    for i,u in enumerate(squad):
        col = "#FFC300" if i==0 else "#1f77b4"
        if u["alive"]: ax.scatter(u["x"], u["y"], s=300, color=col, edgecolors="black", zorder=4); ax.text(u["x"], u["y"], "C" if i==0 else str(i), ha="center", va="center", fontsize=7, zorder=5)
        else: ax.scatter(u["x"], u["y"], s=160, color="#999", marker="x", zorder=4)
    ax.set_title("Arma 3 live | squad(bleu) vs OPFOR(rouge) | dans_obj %d vivants %d" % (in_obj, alive), fontsize=9)
FuncAnimation(fig, draw, frames=frames, interval=400).save("arma_capture.gif", writer=PillowWriter(fps=3))
print("GIF: arma_capture.gif (%d images)" % len(frames))
