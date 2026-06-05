"""Harmattan v2 — hiérarchie : le CHEF (manager) assigne une tâche discrète à chaque
spécialiste ; les 3 spécialistes exécutent, conditionnés par leur tâche. Critique central.
Tâches (étiquettes ; le worker apprend leur sens) : 0=avancer 1=suppresser 2=relever 3=tenir."""
import os, json, csv, argparse
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from torch.distributions import Categorical
from datetime import datetime
from toy2d_v1 import VectorizedToy2Dv1, ALIVE, DOWN, DEAD
from train_harmattan import desktop_root

N_TASKS, N_SPEC = 4, 3  # chef = agent 0 ; specialistes = agents 1,2,3

class HierNet(nn.Module):
    def __init__(self, O, n_act, A, h=64):
        super().__init__(); self.O, self.A = O, A
        self.worker = nn.Sequential(nn.Linear(O + N_TASKS, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, n_act))
        self.manager = nn.Sequential(nn.Linear(O * A, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, N_SPEC * N_TASKS))
        self.critic = nn.Sequential(nn.Linear(O * A, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))
    def mdist(self, glob): return Categorical(logits=self.manager(glob).view(-1, N_SPEC, N_TASKS))
    def wdist(self, obs, to): return Categorical(logits=self.worker(torch.cat([obs, to], -1)))
    def value(self, glob): return self.critic(glob).squeeze(-1)

def tasks_to_oh(tasks, N, A, dev):  # tasks (N,3) -> (N,A,N_TASKS), chef=0
    to = torch.zeros(N, A, N_TASKS, device=dev); to[:, 1:, :] = F.one_hot(tasks, N_TASKS).float(); return to

def render_v2(net, dev, path, seed=7):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation, PillowWriter
    env = VectorizedToy2Dv1(num_envs=1, seed=seed); env.reset()
    TL = ["AV", "SUP", "REL", "TEN"]; rcol = ["#FFC300", "#1f77b4", "#2ca02c", "#9467bd"]; rlab = ["C", "Mi", "Md", "Ec"]
    frames = []
    cur = np.zeros(3, dtype=int)
    for _ in range(env.max_steps):
        frames.append((env.pos[0].copy(), env.state[0].copy(), env.suppress_t[0].copy(), bool(env.success[0]), int(env.t[0]), cur.copy()))
        if env.done[0]: break
        o = torch.as_tensor(env._get_obs(), dtype=torch.float32, device=dev)
        with torch.no_grad():
            glob = o.reshape(1, -1); tasks = net.mdist(glob).logits.argmax(-1)  # (1,3)
            to = tasks_to_oh(tasks, 1, env.A, dev)
            a = net.wdist(o, to).logits.argmax(-1).cpu().numpy()
        cur = tasks[0].cpu().numpy()
        env.step(a, auto_reset=False)
    frames.append((env.pos[0].copy(), env.state[0].copy(), env.suppress_t[0].copy(), bool(env.success[0]), int(env.t[0]), cur.copy()))
    G = env.G; fig, ax = plt.subplots(figsize=(6, 6))
    def draw(fr):
        pos, state, supp, success, step, tk = fr; ax.clear()
        ax.set_xlim(-0.5, G - 0.5); ax.set_ylim(G - 0.5, -0.5); ax.set_xticks(range(G)); ax.set_yticks(range(G)); ax.grid(True, color="#ddd", lw=0.5); ax.set_aspect("equal")
        lo, hi = env.obj_lo, env.obj_hi
        ax.add_patch(patches.Rectangle((lo[1]-0.5, lo[0]-0.5), hi[1]-lo[1]+1, hi[0]-lo[0]+1, color="#2ca02c", alpha=0.22))
        ax.text(env.obj_center[1], env.obj_center[0], "OBJ", ha="center", va="center", color="#1a7a1a", fontsize=9, fontweight="bold")
        for di, d in enumerate(env.danger):
            sd = supp[di] > 0; ax.add_patch(patches.Rectangle((d[1]-0.5, d[0]-0.5), 1, 1, color="#ffe680" if sd else "#d62728", alpha=0.6 if sd else 0.32))
        for i in range(env.A):
            r, c = pos[i]; lbl = rlab[i]
            if i >= 1: lbl = rlab[i] + ":" + TL[tk[i-1]]
            if state[i] == ALIVE:
                ax.scatter(c, r, s=340, color=rcol[i], edgecolors="black", zorder=3); ax.text(c, r-0.0, rlab[i], ha="center", va="center", fontsize=7, zorder=4)
                ax.text(c, r+0.42, lbl, ha="center", va="bottom", fontsize=5.5, color="#222", zorder=5)
            elif state[i] == DOWN:
                ax.scatter(c, r, s=300, color="#ff7f0e", edgecolors="red", linewidths=1.5, zorder=3)
            else:
                ax.scatter(c, r, s=200, color="#999", marker="x", zorder=3)
        na = int((state == ALIVE).sum()); dd = int((state == DEAD).sum())
        t = f"v2 chef-manager | pas {step}/{env.max_steps} | vivants {na} morts {dd}"
        if success: t += " | OBJ SECURISE"
        ax.set_title(t, fontsize=9)
    FuncAnimation(fig, draw, frames=frames, interval=300).save(path, writer=PillowWriter(fps=3)); plt.close(fig)
    return frames[-1][3], int((frames[-1][1] == DEAD).sum())

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements")
    rid = datetime.now().strftime("run_v2_%Y%m%d_%H%M%S"); rd = os.path.join(root, rid); os.makedirs(rd, exist_ok=True)
    json.dump(cfg, open(os.path.join(rd, "config.json"), "w"), indent=2); print(f"[run v2] {rd} | {dev}")
    env = VectorizedToy2Dv1(num_envs=cfg["envs"], seed=cfg["seed"]); obs = env.reset(); N, A, O = obs.shape
    net = HierNet(O, env.n_actions, A, cfg["hidden"]).to(dev); opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    if cfg["gif"]: s, c = render_v2(net, dev, os.path.join(rd, "avant.gif")); print(f"[avant] succes={s} morts={c}")
    T, gamma, lam, cp = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    held = torch.zeros(N, N_SPEC, dtype=torch.long, device=dev); held_lpm = torch.zeros(N, N_SPEC, device=dev); mgr_timer = np.zeros(N, dtype=int)
    ep_r = np.zeros(N); ep_c = np.zeros(N); rs, rc, rr = [], [], []; gs = 0; hist = []
    for it in range(cfg["iters"]):
        B_obs = torch.zeros(T, N, A, O, device=dev); B_tk = torch.zeros(T, N, N_SPEC, dtype=torch.long, device=dev)
        B_mv = torch.zeros(T, N, A, dtype=torch.long, device=dev); B_lpm = torch.zeros(T, N, N_SPEC, device=dev)
        B_lpw = torch.zeros(T, N, A, device=dev); B_v = torch.zeros(T, N, device=dev); B_r = torch.zeros(T, N, device=dev); B_d = torch.zeros(T, N, device=dev); B_dec = torch.zeros(T, N, device=dev)
        for t in range(T):
            glob = obs_t.reshape(N, A * O)
            decide = mgr_timer <= 0; dec_t = torch.as_tensor(decide, device=dev).unsqueeze(1)
            with torch.no_grad():
                md = net.mdist(glob); samp = md.sample(); slp = md.log_prob(samp)
                held = torch.where(dec_t, samp, held); held_lpm = torch.where(dec_t, slp, held_lpm)
                to = tasks_to_oh(held, N, A, dev); wd = net.wdist(obs_t, to); mv = wd.sample(); lpw = wd.log_prob(mv); v = net.value(glob)
            nobs, rew, cost, done, info = env.step(mv.cpu().numpy())
            B_obs[t] = obs_t; B_tk[t] = held; B_mv[t] = mv; B_lpm[t] = held_lpm; B_lpw[t] = lpw; B_v[t] = v; B_dec[t] = torch.as_tensor(decide.astype(np.float32), device=dev)
            mgr_timer[decide] = cfg["mgr_period"]; mgr_timer = mgr_timer - 1
            B_r[t] = torch.as_tensor(rew - cp * cost, dtype=torch.float32, device=dev); B_d[t] = torch.as_tensor(done.astype(np.float32), device=dev)
            ep_r += rew; ep_c += cost
            for n in np.where(done)[0]:
                rs.append(float(info["success"][n])); rc.append(ep_c[n]); rr.append(ep_r[n]); ep_r[n] = 0; ep_c[n] = 0
            mgr_timer[done] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gs += N
        with torch.no_grad(): last_v = net.value(obs_t.reshape(N, A * O))
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - B_d[t]; nv = last_v if t == T - 1 else B_v[t + 1]
            d = B_r[t] + gamma * nv * nnt - B_v[t]; g = d + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + B_v).reshape(T * N)
        f_obs = B_obs.reshape(T * N, A, O); f_glob = f_obs.reshape(T * N, A * O); f_tk = B_tk.reshape(T * N, N_SPEC)
        f_mv = B_mv.reshape(T * N, A); f_lpm = B_lpm.reshape(T * N, N_SPEC); f_lpw = B_lpw.reshape(T * N, A); f_dec = B_dec.reshape(T * N)
        fa = adv.reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"]); pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); av = fa[j].unsqueeze(1)
                to = tasks_to_oh(f_tk[j], len(j), A, dev); wd = net.wdist(f_obs[j], to); nlpw = wd.log_prob(f_mv[j]); rw = torch.exp(nlpw - f_lpw[j])
                plw = -torch.min(rw * av, torch.clamp(rw, 1 - cfg["clip"], 1 + cfg["clip"]) * av).mean()
                dj = j[f_dec[j] > 0.5]
                if dj.numel() > 0:
                    md = net.mdist(f_glob[dj]); nlpm = md.log_prob(f_tk[dj]); rm = torch.exp(nlpm - f_lpm[dj]); avm = fa[dj].unsqueeze(1)
                    plm = -torch.min(rm * avm, torch.clamp(rm, 1 - cfg["clip"], 1 + cfg["clip"]) * avm).mean(); entm = md.entropy().mean()
                else:
                    plm = torch.zeros((), device=dev); entm = torch.zeros((), device=dev)
                vloss = ((net.value(f_glob[j]) - ret[j]) ** 2).mean(); ent = entm + wd.entropy().mean()
                loss = plm + plw + cfg["vf"] * vloss - cfg["ent"] * ent
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                pl += (plm + plw).item(); vl += vloss.item(); en += ent.item(); nu += 1
        tm = lambda x: float(np.mean(x[-300:])) if x else float("nan")
        row = dict(iter=it, steps=gs, success_rate=tm(rs), casualties=tm(rc), ep_return=tm(rr), ploss=pl / nu, vloss=vl / nu, entropy=en / nu)
        hist.append(row)
        if it % max(1, cfg["iters"] // 20) == 0 or it == cfg["iters"] - 1:
            print(f"it {it:4d} | succes {row['success_rate']:.2f} | morts/ep {row['casualties']:.2f} | retour {row['ep_return']:+.2f} | ent {row['entropy']:.2f}")
    with open(os.path.join(rd, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(rd, "model.pt"))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_title("Reussite (v2 chef)"); ax[0].set_ylim(-0.05, 1.05)
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].set_title("Morts def. / episode"); fig.tight_layout(); fig.savefig(os.path.join(rd, "courbes.png")); plt.close(fig)
    except Exception as e: print("courbes:", e)
    if cfg["gif"]: s, c = render_v2(net, dev, os.path.join(rd, "apres.gif")); print(f"[apres] succes={s} morts={c}")
    idxf = os.path.join(root, "index.csv"); newf = not os.path.exists(idxf)
    with open(idxf, "a", newline="") as f:
        w = csv.writer(f)
        if newf: w.writerow(["run", "iters", "envs", "success_final", "casualties_final", "cas_pen"])
        w.writerow([rid, cfg["iters"], cfg["envs"], f"{hist[-1]['success_rate']:.3f}", f"{hist[-1]['casualties']:.3f}", cfg["cas_pen"]])
    print(f"[fini] reussite={hist[-1]['success_rate']:.2f} morts/ep={hist[-1]['casualties']:.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("iters",600,int),("envs",512,int),("rollout",32,int),("hidden",64,int),("lr",3e-4,float),("gamma",0.99,float),("gae",0.95,float),("clip",0.2,float),("epochs",4,int),("minibatches",4,int),("vf",0.5,float),("ent",0.01,float),("seed",0,int),("cas_pen",0.5,float),("mgr_period",8,int)]:
        p.add_argument("--"+k.replace("_","-"), default=v, type=t, dest=k)
    p.add_argument("--no-gif", action="store_true")
    a = p.parse_args(); cfg = vars(a); cfg["gif"] = not cfg.pop("no_gif"); train(cfg)
