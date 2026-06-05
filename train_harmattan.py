"""Harmattan — entraînement MAPPO simplifié (PPO à politique partagée + critique central).
Chaque run crée un dossier d'historique : config, history.csv, courbes, GIF avant/après, modèle.
Récompense d'entraînement = récompense d'équipe - cas_pen * pertes (scalarisation simple ;
le vrai CMDP/lambda viendra à l'étape 3)."""
import os, sys, json, time, argparse, subprocess
import numpy as np
import torch, torch.nn as nn
from torch.distributions import Categorical
from datetime import datetime
from toy2d import VectorizedToy2D

def desktop_root():
    try:
        d = subprocess.check_output(["xdg-user-dir", "DESKTOP"], text=True).strip()
        if d and os.path.isdir(d):
            return d
    except Exception:
        pass
    for c in ["~/Bureau", "~/Desktop"]:
        p = os.path.expanduser(c)
        if os.path.isdir(p):
            return p
    p = os.path.expanduser("~/Desktop"); os.makedirs(p, exist_ok=True); return p

class ActorCritic(nn.Module):
    def __init__(self, obs_dim, n_actions, n_agents, hidden=64):
        super().__init__()
        self.actor = nn.Sequential(nn.Linear(obs_dim, hidden), nn.Tanh(),
                                   nn.Linear(hidden, hidden), nn.Tanh(),
                                   nn.Linear(hidden, n_actions))
        self.critic = nn.Sequential(nn.Linear(obs_dim * n_agents, hidden), nn.Tanh(),
                                    nn.Linear(hidden, hidden), nn.Tanh(),
                                    nn.Linear(hidden, 1))
    def act(self, obs):
        dist = Categorical(logits=self.actor(obs)); a = dist.sample()
        return a, dist.log_prob(a)
    def value(self, obs):
        B, A, O = obs.shape
        return self.critic(obs.reshape(B, A * O)).squeeze(-1)
    def evaluate(self, obs, actions):
        dist = Categorical(logits=self.actor(obs))
        return dist.log_prob(actions), dist.entropy()

def render_gif(net, dev, path, seed=7, max_steps=100):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation, PillowWriter
    env = VectorizedToy2D(num_envs=1, seed=seed); env.reset()
    frames = []
    for _ in range(max_steps):
        frames.append((env.pos[0].copy(), env.alive[0].copy(), bool(env.success[0]), int(env.t[0])))
        if env.done[0]:
            break
        o = torch.as_tensor(env._get_obs(), dtype=torch.float32, device=dev)
        with torch.no_grad():
            a = net.actor(o).argmax(-1).cpu().numpy()
        env.step(a, auto_reset=False)
    frames.append((env.pos[0].copy(), env.alive[0].copy(), bool(env.success[0]), int(env.t[0])))
    G = env.G; fig, ax = plt.subplots(figsize=(6, 6))
    colors = ["#FFC300", "#1f77b4", "#2ca02c", "#9467bd"]; labels = ["C", "1", "2", "3"]
    def draw(fr):
        pos, alive, success, step = fr; ax.clear()
        ax.set_xlim(-0.5, G - 0.5); ax.set_ylim(G - 0.5, -0.5)
        ax.set_xticks(range(G)); ax.set_yticks(range(G)); ax.grid(True, color="#ddd", linewidth=0.5); ax.set_aspect("equal")
        lo, hi = env.obj_lo, env.obj_hi
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
                ax.scatter(c, r, s=200, color="#999", marker="x", zorder=3)
        nd = int((~alive).sum()); t = f"pas {step}/{env.max_steps}  |  pertes: {nd}/{env.A}"
        if success: t += "  |  OBJECTIF SECURISE"
        ax.set_title(t, fontsize=10)
    FuncAnimation(fig, draw, frames=frames, interval=300).save(path, writer=PillowWriter(fps=3))
    plt.close(fig)
    return frames[-1][2], int((~frames[-1][1]).sum())

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements")
    rid = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = os.path.join(root, rid); os.makedirs(run_dir, exist_ok=True)
    json.dump(cfg, open(os.path.join(run_dir, "config.json"), "w"), indent=2)
    print(f"[run] {run_dir}  | device={dev}")
    env = VectorizedToy2D(num_envs=cfg["envs"], seed=cfg["seed"])
    obs = env.reset(); N, A, O = obs.shape
    net = ActorCritic(O, env.n_actions, A, cfg["hidden"]).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    if cfg["gif"]:
        s, c = render_gif(net, dev, os.path.join(run_dir, "avant.gif"))
        print(f"[gif avant] succes={s} pertes={c}/{A}")
    T, gamma, lam, cp = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    ep_ret = np.zeros(N); ep_cas = np.zeros(N)
    rs, rc, rr = [], [], []; gstep = 0; hist = []
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
                rs.append(float(info["success"][n])); rc.append(ep_cas[n]); rr.append(ep_ret[n])
                ep_ret[n] = 0; ep_cas[n] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gstep += N
        with torch.no_grad():
            last_v = net.value(obs_t)
        adv = torch.zeros(T, N, device=dev); gae = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1.0 - b_done[t]; nv = last_v if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + gamma * nv * nnt - b_val[t]
            gae = delta + gamma * lam * nnt * gae; adv[t] = gae
        ret = (adv + b_val).reshape(T * N)
        f_obs = b_obs.reshape(T * N, A, O); f_act = b_act.reshape(T * N, A); f_logp = b_logp.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8)
        f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"])
        pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev)
                o = f_obs[j]; nlp, ent = net.evaluate(o, f_act[j])
                ratio = torch.exp(nlp - f_logp[j]); a_ = f_adv[j]
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
                vloss = ((net.value(o) - ret[j]) ** 2).mean(); entropy = ent.mean()
                loss = ploss + cfg["vf"] * vloss - cfg["ent"] * entropy
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                pl += ploss.item(); vl += vloss.item(); en += entropy.item(); nu += 1
        tm = lambda x: float(np.mean(x[-300:])) if x else float("nan")
        row = dict(iter=it, steps=gstep, success_rate=tm(rs), casualties=tm(rc), ep_return=tm(rr),
                   ploss=pl / nu, vloss=vl / nu, entropy=en / nu)
        hist.append(row)
        if it % max(1, cfg["iters"] // 20) == 0 or it == cfg["iters"] - 1:
            print(f"it {it:4d} | steps {gstep:8d} | succes {row['success_rate']:.2f} | pertes/ep {row['casualties']:.2f} | retour {row['ep_return']:+.2f} | ent {row['entropy']:.2f}")
    # sauvegardes
    import csv
    with open(os.path.join(run_dir, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(run_dir, "model.pt"))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_title("Taux de reussite"); ax[0].set_ylim(-0.05, 1.05); ax[0].set_xlabel("iteration")
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].set_title("Pertes moy. / episode"); ax[1].set_xlabel("iteration")
        fig.tight_layout(); fig.savefig(os.path.join(run_dir, "courbes.png")); plt.close(fig)
    except Exception as e:
        print("courbes:", e)
    if cfg["gif"]:
        s, c = render_gif(net, dev, os.path.join(run_dir, "apres.gif"))
        print(f"[gif apres] succes={s} pertes={c}/{A}")
    # index global des runs
    idxf = os.path.join(root, "index.csv"); newf = not os.path.exists(idxf)
    with open(idxf, "a", newline="") as f:
        import csv as _c; w = _c.writer(f)
        if newf: w.writerow(["run", "iters", "envs", "success_final", "casualties_final", "cas_pen"])
        w.writerow([rid, cfg["iters"], cfg["envs"], f"{hist[-1]['success_rate']:.3f}", f"{hist[-1]['casualties']:.3f}", cfg["cas_pen"]])
    print(f"[fini] {run_dir}\n  reussite finale={hist[-1]['success_rate']:.2f} | pertes/ep={hist[-1]['casualties']:.2f}")
    return run_dir

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=400); p.add_argument("--envs", type=int, default=512)
    p.add_argument("--rollout", type=int, default=32); p.add_argument("--hidden", type=int, default=64)
    p.add_argument("--lr", type=float, default=3e-4); p.add_argument("--cas-pen", type=float, default=0.5, dest="cas_pen")
    p.add_argument("--gamma", type=float, default=0.99); p.add_argument("--gae", type=float, default=0.95)
    p.add_argument("--clip", type=float, default=0.2); p.add_argument("--epochs", type=int, default=4)
    p.add_argument("--minibatches", type=int, default=4); p.add_argument("--vf", type=float, default=0.5)
    p.add_argument("--ent", type=float, default=0.01); p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no-gif", action="store_true")
    a = p.parse_args(); cfg = vars(a); cfg["gif"] = not cfg.pop("no_gif")
    train(cfg)
