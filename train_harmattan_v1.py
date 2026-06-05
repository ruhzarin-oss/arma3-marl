"""Harmattan v1 — entraînement avec rôles (politique partagée CONDITIONNÉE PAR LE RÔLE)."""
import os, json, csv, argparse
import numpy as np
import torch, torch.nn as nn
from datetime import datetime
from toy2d_v1 import VectorizedToy2Dv1, ALIVE, DOWN, DEAD
import numpy as _np
class NoRolesEnv(VectorizedToy2Dv1):
    def step(self, actions, auto_reset=True):
        return super().step(_np.where(actions == 5, 0, actions), auto_reset)
def _envcls(roles):
    return VectorizedToy2Dv1 if roles else NoRolesEnv
from train_harmattan import ActorCritic, desktop_root

def render_gif_v1(net, dev, path, seed=7, roles_enabled=True):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation, PillowWriter
    env = _envcls(roles_enabled)(num_envs=1, seed=seed); env.reset()
    frames = []
    def snap(): return (env.pos[0].copy(), env.state[0].copy(), env.suppress_t[0].copy(), bool(env.success[0]), int(env.t[0]))
    for _ in range(env.max_steps):
        frames.append(snap())
        if env.done[0]: break
        o = torch.as_tensor(env._get_obs(), dtype=torch.float32, device=dev)
        with torch.no_grad():
            a = net.actor(o).argmax(-1).cpu().numpy()
        env.step(a, auto_reset=False)
    frames.append(snap())
    G = env.G; fig, ax = plt.subplots(figsize=(6, 6))
    rcol = ["#FFC300", "#1f77b4", "#2ca02c", "#9467bd"]; rlab = ["C", "Mi", "Md", "Ec"]
    def draw(fr):
        pos, state, supp, success, step = fr; ax.clear()
        ax.set_xlim(-0.5, G - 0.5); ax.set_ylim(G - 0.5, -0.5)
        ax.set_xticks(range(G)); ax.set_yticks(range(G)); ax.grid(True, color="#ddd", lw=0.5); ax.set_aspect("equal")
        lo, hi = env.obj_lo, env.obj_hi
        ax.add_patch(patches.Rectangle((lo[1]-0.5, lo[0]-0.5), hi[1]-lo[1]+1, hi[0]-lo[0]+1, color="#2ca02c", alpha=0.22))
        ax.text(env.obj_center[1], env.obj_center[0], "OBJ", ha="center", va="center", color="#1a7a1a", fontsize=9, fontweight="bold")
        for di, d in enumerate(env.danger):
            supd = supp[di] > 0
            ax.add_patch(patches.Rectangle((d[1]-0.5, d[0]-0.5), 1, 1, color="#ffe680" if supd else "#d62728", alpha=0.6 if supd else 0.32))
        for i in range(env.A):
            r, c = pos[i]
            if state[i] == ALIVE:
                ax.scatter(c, r, s=340, color=rcol[i], edgecolors="black", zorder=3); ax.text(c, r, rlab[i], ha="center", va="center", fontsize=7, zorder=4)
            elif state[i] == DOWN:
                ax.scatter(c, r, s=300, color="#ff7f0e", edgecolors="red", linewidths=1.5, zorder=3); ax.text(c, r, rlab[i], ha="center", va="center", fontsize=6, zorder=4)
            else:
                ax.scatter(c, r, s=200, color="#999", marker="x", zorder=3)
        na = int((state == ALIVE).sum()); nd = int((state == DOWN).sum()); dd = int((state == DEAD).sum())
        t = f"v1 roles | pas {step}/{env.max_steps} | vivants {na} a-terre {nd} morts {dd}"
        if success: t += " | OBJ SECURISE"
        ax.set_title(t, fontsize=9)
    FuncAnimation(fig, draw, frames=frames, interval=300).save(path, writer=PillowWriter(fps=3))
    plt.close(fig)
    return frames[-1][3], int((frames[-1][1] == DEAD).sum())

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements")
    rid = datetime.now().strftime(("run_v1_" if cfg["roles_enabled"] else "run_v1noroles_") + "%Y%m%d_%H%M%S"); run_dir = os.path.join(root, rid); os.makedirs(run_dir, exist_ok=True)
    json.dump(cfg, open(os.path.join(run_dir, "config.json"), "w"), indent=2)
    print(f"[run v1] {run_dir} | device={dev}")
    env = _envcls(cfg["roles_enabled"])(num_envs=cfg["envs"], seed=cfg["seed"]); obs = env.reset(); N, A, O = obs.shape
    net = ActorCritic(O, env.n_actions, A, cfg["hidden"]).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    if cfg["gif"]:
        s, c = render_gif_v1(net, dev, os.path.join(run_dir, "avant.gif"), roles_enabled=cfg["roles_enabled"]); print(f"[gif avant] succes={s} morts={c}/{A}")
    T, gamma, lam, cp = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    ep_ret = np.zeros(N); ep_cas = np.zeros(N); rs, rc, rr = [], [], []; gstep = 0; hist = []
    for it in range(cfg["iters"]):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev)
        b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        for t in range(T):
            with torch.no_grad():
                a, logp = net.act(obs_t); v = net.value(obs_t)
            nobs, rew, cost, done, info = env.step(a.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = a; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew - cp * cost, dtype=torch.float32, device=dev)
            b_done[t] = torch.as_tensor(done.astype(np.float32), device=dev)
            ep_ret += rew; ep_cas += cost
            for n in np.where(done)[0]:
                rs.append(float(info["success"][n])); rc.append(ep_cas[n]); rr.append(ep_ret[n]); ep_ret[n] = 0; ep_cas[n] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gstep += N
        with torch.no_grad():
            last_v = net.value(obs_t)
        adv = torch.zeros(T, N, device=dev); gae = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1.0 - b_done[t]; nv = last_v if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + gamma * nv * nnt - b_val[t]; gae = delta + gamma * lam * nnt * gae; adv[t] = gae
        ret = (adv + b_val).reshape(T * N)
        f_obs = b_obs.reshape(T * N, A, O); f_act = b_act.reshape(T * N, A); f_logp = b_logp.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8); f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"]); pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); o = f_obs[j]
                nlp, ent = net.evaluate(o, f_act[j]); ratio = torch.exp(nlp - f_logp[j]); a_ = f_adv[j]
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
                vloss = ((net.value(o) - ret[j]) ** 2).mean(); entropy = ent.mean()
                loss = ploss + cfg["vf"] * vloss - cfg["ent"] * entropy
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                pl += ploss.item(); vl += vloss.item(); en += entropy.item(); nu += 1
        tm = lambda x: float(np.mean(x[-300:])) if x else float("nan")
        row = dict(iter=it, steps=gstep, success_rate=tm(rs), casualties=tm(rc), ep_return=tm(rr), ploss=pl/nu, vloss=vl/nu, entropy=en/nu)
        hist.append(row)
        if it % max(1, cfg["iters"]//20) == 0 or it == cfg["iters"]-1:
            print(f"it {it:4d} | steps {gstep:8d} | succes {row['success_rate']:.2f} | morts/ep {row['casualties']:.2f} | retour {row['ep_return']:+.2f} | ent {row['entropy']:.2f}")
    with open(os.path.join(run_dir, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(run_dir, "model.pt"))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_title("Taux de reussite (v1 roles)"); ax[0].set_ylim(-0.05, 1.05); ax[0].set_xlabel("iteration")
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].set_title("Morts def. / episode"); ax[1].set_xlabel("iteration")
        fig.tight_layout(); fig.savefig(os.path.join(run_dir, "courbes.png")); plt.close(fig)
    except Exception as e:
        print("courbes:", e)
    if cfg["gif"]:
        s, c = render_gif_v1(net, dev, os.path.join(run_dir, "apres.gif"), roles_enabled=cfg["roles_enabled"]); print(f"[gif apres] succes={s} morts={c}/{A}")
    idxf = os.path.join(root, "index.csv"); newf = not os.path.exists(idxf)
    with open(idxf, "a", newline="") as f:
        w = csv.writer(f)
        if newf: w.writerow(["run", "iters", "envs", "success_final", "casualties_final", "cas_pen"])
        w.writerow([rid, cfg["iters"], cfg["envs"], f"{hist[-1]['success_rate']:.3f}", f"{hist[-1]['casualties']:.3f}", cfg["cas_pen"]])
    print(f"[fini] {run_dir}\n  reussite finale={hist[-1]['success_rate']:.2f} | morts/ep={hist[-1]['casualties']:.2f}")
    return run_dir

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("iters",600,int),("envs",512,int),("rollout",32,int),("hidden",64,int),("lr",3e-4,float),
                    ("gamma",0.99,float),("gae",0.95,float),("clip",0.2,float),("epochs",4,int),
                    ("minibatches",4,int),("vf",0.5,float),("ent",0.01,float),("seed",0,int),("cas_pen",0.5,float)]:
        p.add_argument("--"+k.replace("_","-"), default=v, type=t, dest=k)
    p.add_argument("--no-gif", action="store_true")
    p.add_argument("--no-roles", action="store_true")
    a = p.parse_args(); cfg = vars(a); cfg["gif"] = not cfg.pop("no_gif"); cfg["roles_enabled"] = not cfg.pop("no_roles")
    train(cfg)
