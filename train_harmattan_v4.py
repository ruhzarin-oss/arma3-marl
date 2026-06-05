"""Harmattan v4 — entraînement PLAT (MAPPO partagé) avec doctrine de cohésion. Pas de manager."""
import os, json, csv, argparse
import numpy as np, torch, torch.nn as nn
from datetime import datetime
from toy2d_v4 import VectorizedToy2Dv4
from train_harmattan import ActorCritic, desktop_root

def render_v4(net, dev, path, seed=7):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation, PillowWriter
    env = VectorizedToy2Dv4(num_envs=1, seed=seed); env.reset(); frames = []
    def snap(): return (env.pos[0].copy(), env.alive[0].copy(), int(env.gap[0]), bool(env.success[0]), int(env.t[0]), float(env._cohesion()[0]))
    for _ in range(env.max_steps):
        frames.append(snap())
        if env.done[0]: break
        o = torch.as_tensor(env._get_obs(), dtype=torch.float32, device=dev)
        with torch.no_grad(): a = net.actor(o).argmax(-1).cpu().numpy()
        env.step(a, auto_reset=False)
    frames.append(snap()); G = env.G; fig, ax = plt.subplots(figsize=(6, 6))
    col = ["#FFC300", "#1f77b4", "#2ca02c", "#9467bd"]; lab = ["CHEF", "S1", "S2", "S3"]
    def draw(fr):
        pos, alive, gap, success, step, coh = fr; ax.clear()
        ax.set_xlim(-0.5, G-0.5); ax.set_ylim(G-0.5, -0.5); ax.set_xticks(range(G)); ax.set_yticks(range(G)); ax.grid(True, color="#eee", lw=0.4); ax.set_aspect("equal")
        lo, hi = env.obj_lo, env.obj_hi
        ax.add_patch(patches.Rectangle((lo[1]-0.5, lo[0]-0.5), hi[1]-lo[1]+1, hi[0]-lo[0]+1, color="#2ca02c", alpha=0.25)); ax.text(env.obj_c[1], env.obj_c[0], "OBJ", ha="center", va="center", color="#1a7a1a", fontsize=8, fontweight="bold")
        for c in range(G):
            if not (gap <= c < gap + env.gapw): ax.add_patch(patches.Rectangle((c-0.5, env.drow-0.5), 1, 1, color="#d62728", alpha=0.35))
        for i in range(env.A):
            r, c = pos[i]
            if alive[i]: ax.scatter(c, r, s=420 if i == 0 else 280, color=col[i], edgecolors="black", zorder=3); ax.text(c, r, "C" if i == 0 else str(i), ha="center", va="center", fontsize=7, zorder=4)
            else: ax.scatter(c, r, s=170, color="#999", marker="x", zorder=3)
        t = f"v4 doctrine 'suivre le chef' | pas {step} | vivants {int(alive.sum())}/4 | cohesion {coh:.2f}"
        if success: t += " | SECURISE"
        ax.set_title(t, fontsize=9)
    FuncAnimation(fig, draw, frames=frames, interval=300).save(path, writer=PillowWriter(fps=3)); plt.close(fig)
    return frames[-1][3], int((~frames[-1][1]).sum())

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements"); rid = datetime.now().strftime("run_v4_%Y%m%d_%H%M%S"); rd = os.path.join(root, rid); os.makedirs(rd, exist_ok=True)
    json.dump(cfg, open(os.path.join(rd, "config.json"), "w"), indent=2); print(f"[run v4] {rd} | {dev}")
    env = VectorizedToy2Dv4(num_envs=cfg["envs"], seed=cfg["seed"]); obs = env.reset(); N, A, O = obs.shape
    net = ActorCritic(O, env.n_actions, A, cfg["hidden"]).to(dev); opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    if cfg["gif"]: s, c = render_v4(net, dev, os.path.join(rd, "avant.gif")); print(f"[avant] succes={s} morts={c}")
    T, gamma, lam, cp = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    ep_r = np.zeros(N); ep_c = np.zeros(N); ep_h = np.zeros(N); ep_l = np.zeros(N); rs, rc, rh = [], [], []; gs = 0; hist = []
    for it in range(cfg["iters"]):
        Bo = torch.zeros(T, N, A, O, device=dev); Ba = torch.zeros(T, N, A, dtype=torch.long, device=dev); Blp = torch.zeros(T, N, A, device=dev)
        Br = torch.zeros(T, N, device=dev); Bv = torch.zeros(T, N, device=dev); Bd = torch.zeros(T, N, device=dev)
        for t in range(T):
            with torch.no_grad(): a, lp = net.act(obs_t); v = net.value(obs_t)
            nobs, rew, cost, done, info = env.step(a.cpu().numpy())
            Bo[t] = obs_t; Ba[t] = a; Blp[t] = lp; Bv[t] = v
            Br[t] = torch.as_tensor(rew - cp * cost, dtype=torch.float32, device=dev); Bd[t] = torch.as_tensor(done.astype(np.float32), device=dev)
            ep_r += rew; ep_c += cost; ep_h += info["cohesion"]; ep_l += 1
            for n in np.where(done)[0]:
                rs.append(float(info["success"][n])); rc.append(ep_c[n]); rh.append(ep_h[n] / max(ep_l[n], 1)); ep_r[n] = 0; ep_c[n] = 0; ep_h[n] = 0; ep_l[n] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gs += N
        with torch.no_grad(): last_v = net.value(obs_t)
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - Bd[t]; nv = last_v if t == T - 1 else Bv[t + 1]; d = Br[t] + gamma * nv * nnt - Bv[t]; g = d + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + Bv).reshape(T * N); f_obs = Bo.reshape(T * N, A, O); f_a = Ba.reshape(T * N, A); f_lp = Blp.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8); f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"]); pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); o = f_obs[j]
                nlp, ent = net.evaluate(o, f_a[j]); ratio = torch.exp(nlp - f_lp[j]); a_ = f_adv[j]
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
                vloss = ((net.value(o) - ret[j]) ** 2).mean(); entropy = ent.mean(); loss = ploss + cfg["vf"] * vloss - cfg["ent"] * entropy
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                pl += ploss.item(); vl += vloss.item(); en += entropy.item(); nu += 1
        tm = lambda x: float(np.mean(x[-300:])) if x else float("nan")
        row = dict(iter=it, steps=gs, success_rate=tm(rs), casualties=tm(rc), cohesion=tm(rh), entropy=en / nu); hist.append(row)
        if it % max(1, cfg["iters"] // 20) == 0 or it == cfg["iters"] - 1:
            print(f"it {it:4d} | succes {row['success_rate']:.2f} | morts/ep {row['casualties']:.2f} | cohesion {row['cohesion']:.2f} | ent {row['entropy']:.2f}")
    with open(os.path.join(rd, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(rd, "model.pt"))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_title("Reussite"); ax[0].set_ylim(-0.05, 1.05)
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].set_title("Morts/ep")
        ax[2].plot(its, [h["cohesion"] for h in hist], color="blue"); ax[2].set_title("Cohesion (suivre le chef)"); ax[2].set_ylim(0, 1)
        fig.tight_layout(); fig.savefig(os.path.join(rd, "courbes.png")); plt.close(fig)
    except Exception as e: print("courbes:", e)
    if cfg["gif"]: s, c = render_v4(net, dev, os.path.join(rd, "apres.gif")); print(f"[apres] succes={s} morts={c}")
    print(f"[fini] reussite={hist[-1]['success_rate']:.2f} morts/ep={hist[-1]['casualties']:.2f} cohesion={hist[-1]['cohesion']:.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("iters",600,int),("envs",512,int),("rollout",32,int),("hidden",64,int),("lr",3e-4,float),("gamma",0.99,float),("gae",0.95,float),("clip",0.2,float),("epochs",4,int),("minibatches",4,int),("vf",0.5,float),("ent",0.01,float),("seed",0,int),("cas_pen",0.5,float)]:
        p.add_argument("--"+k.replace("_","-"), default=v, type=t, dest=k)
    p.add_argument("--no-gif", action="store_true")
    a = p.parse_args(); cfg = vars(a); cfg["gif"] = not cfg.pop("no_gif"); train(cfg)
