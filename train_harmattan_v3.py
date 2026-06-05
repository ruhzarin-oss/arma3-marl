"""Harmattan v3 — chef-sergent ARBITRE : choisit l'objectif (gauche/droite), tenu K pas ;
toute l'équipe (chef compris) y converge. Curriculum : level 0 (sans danger) puis level 1."""
import os, json, csv, argparse
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from torch.distributions import Categorical
from datetime import datetime
from toy2d_v3 import VectorizedToy2Dv3
from train_harmattan import desktop_root

class HierNetV3(nn.Module):
    def __init__(self, O, n_act, A, n_obj, h=64):
        super().__init__(); self.A = A; self.n_obj = n_obj
        self.worker = nn.Sequential(nn.Linear(O + n_obj, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, n_act))
        self.manager = nn.Sequential(nn.Linear(O * A, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, n_obj))
        self.critic = nn.Sequential(nn.Linear(O * A, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))
    def mdist(self, glob): return Categorical(logits=self.manager(glob))
    def wdist(self, obs, to): return Categorical(logits=self.worker(torch.cat([obs, to], -1)))
    def value(self, glob): return self.critic(glob).squeeze(-1)

def tgt_oh(target, N, A, centers, dev):
    return centers[target].unsqueeze(1).expand(N, A, 2)

def render_v3(net, dev, path, seed=7, level=1):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation, PillowWriter
    env = VectorizedToy2Dv3(num_envs=1, level=level, seed=seed); env.reset()
    centers = torch.tensor(np.stack([env.objL_c, env.objR_c]) / (env.G - 1), dtype=torch.float32, device=dev)
    rcol = ["#FFC300", "#1f77b4", "#2ca02c", "#9467bd"]; rlab = ["C", "Mi", "Md", "Ec"]
    frames = []; tgt = 0; timer = 0
    def snap(): return (env.pos[0].copy(), env.alive[0].copy(), int(env.blocked[0]), bool(env.success[0]), int(env.t[0]), int(tgt))
    for _ in range(env.max_steps):
        frames.append(snap())
        if env.done[0]: break
        o = torch.as_tensor(env._get_obs(), dtype=torch.float32, device=dev)
        with torch.no_grad():
            if timer <= 0: tgt = int(net.mdist(o.reshape(1, -1)).logits.argmax(-1)[0]); timer = 8
            to = tgt_oh(torch.tensor([tgt], device=dev), 1, env.A, centers, dev)
            a = net.wdist(o, to).logits.argmax(-1).cpu().numpy()
        timer -= 1; env.step(a, auto_reset=False)
    frames.append(snap())
    G = env.G; fig, ax = plt.subplots(figsize=(6, 6))
    def draw(fr):
        pos, alive, blocked, success, step, t = fr; ax.clear()
        ax.set_xlim(-0.5, G-0.5); ax.set_ylim(G-0.5, -0.5); ax.set_xticks(range(G)); ax.set_yticks(range(G)); ax.grid(True, color="#ddd", lw=0.5); ax.set_aspect("equal")
        for lo, hi, name, side in [(env.objL_lo, env.objL_hi, "G", 0), (env.objR_lo, env.objR_hi, "D", 1)]:
            chosen = (t == side)
            ax.add_patch(patches.Rectangle((lo[1]-0.5, lo[0]-0.5), hi[1]-lo[1]+1, hi[0]-lo[0]+1, color="#2ca02c", alpha=0.5 if chosen else 0.18))
            ax.text((lo[1]+hi[1])/2, (lo[0]+hi[0])/2, name, ha="center", va="center", fontweight="bold", color="#1a7a1a", fontsize=9)
        if level >= 1:
            cols = range(0, 5) if blocked == 0 else range(7, G)
            for r in (8, 9):
                for c in cols: ax.add_patch(patches.Rectangle((c-0.5, r-0.5), 1, 1, color="#d62728", alpha=0.3))
        for i in range(env.A):
            r, c = pos[i]
            if alive[i]: ax.scatter(c, r, s=330, color=rcol[i], edgecolors="black", zorder=3); ax.text(c, r, rlab[i], ha="center", va="center", fontsize=7, zorder=4)
            else: ax.scatter(c, r, s=180, color="#999", marker="x", zorder=3)
        na = int(alive.sum())
        tt = f"v3 chef-sergent | pas {step} | ordre chef: {'GAUCHE' if t==0 else 'DROITE'} | vivants {na}/4"
        if success: tt += " | SECURISE"
        ax.set_title(tt, fontsize=9)
    FuncAnimation(fig, draw, frames=frames, interval=300).save(path, writer=PillowWriter(fps=3)); plt.close(fig)
    return frames[-1][3], int((~frames[-1][1]).sum())

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements")
    rid = datetime.now().strftime("run_v3_%Y%m%d_%H%M%S"); rd = os.path.join(root, rid); os.makedirs(rd, exist_ok=True)
    json.dump(cfg, open(os.path.join(rd, "config.json"), "w"), indent=2); print(f"[run v3] {rd} | {dev}")
    env = VectorizedToy2Dv3(num_envs=cfg["envs"], level=0, seed=cfg["seed"]); obs = env.reset(); N, A, O = obs.shape; NO = env.n_obj
    centers = torch.tensor(np.stack([env.objL_c, env.objR_c]) / (env.G - 1), dtype=torch.float32, device=dev)
    net = HierNetV3(O, env.n_actions, A, NO, cfg["hidden"]).to(dev); opt = torch.optim.Adam([{"params": net.manager.parameters(), "lr": cfg["mgr_lr"]}, {"params": net.worker.parameters(), "lr": cfg["lr"]}, {"params": net.critic.parameters(), "lr": cfg["lr"]}])
    if cfg["gif"]: s, c = render_v3(net, dev, os.path.join(rd, "avant.gif"), level=1); print(f"[avant] succes={s} morts={c}")
    T, gamma, lam, cp, K = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"], cfg["mgr_period"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    held = torch.zeros(N, dtype=torch.long, device=dev); held_lpm = torch.zeros(N, device=dev); mgr_timer = np.zeros(N, dtype=int)
    ep_r = np.zeros(N); ep_c = np.zeros(N); rs, rc, rsafe = [], [], []; gs = 0; hist = []
    for it in range(cfg["iters"]):
        if it == cfg["warmup"]: env.set_level(1); print(f"  >>> curriculum: passage NIVEAU 1 (danger) a l'iteration {it}")
        Bo = torch.zeros(T, N, A, O, device=dev); Btk = torch.zeros(T, N, dtype=torch.long, device=dev); Bmv = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        Blpm = torch.zeros(T, N, device=dev); Blpw = torch.zeros(T, N, A, device=dev); Bv = torch.zeros(T, N, device=dev)
        Br = torch.zeros(T, N, device=dev); Bd = torch.zeros(T, N, device=dev); Bdec = torch.zeros(T, N, device=dev)
        for t in range(T):
            glob = obs_t.reshape(N, A * O); decide = mgr_timer <= 0; dt = torch.as_tensor(decide, device=dev)
            with torch.no_grad():
                md = net.mdist(glob); samp = md.sample(); slp = md.log_prob(samp)
                held = torch.where(dt, samp, held); held_lpm = torch.where(dt, slp, held_lpm)
                to = tgt_oh(held, N, A, centers, dev); wd = net.wdist(obs_t, to); mv = wd.sample(); lpw = wd.log_prob(mv); v = net.value(glob)
            if decide.any():
                hn = held.cpu().numpy(); op = 1 - env.blocked; rsafe.extend((hn[decide] == op[decide]).astype(float).tolist())
            nobs, rew, cost, done, info = env.step(mv.cpu().numpy())
            Bo[t] = obs_t; Btk[t] = held; Bmv[t] = mv; Blpm[t] = held_lpm; Blpw[t] = lpw; Bv[t] = v
            Br[t] = torch.as_tensor(rew - cp * cost, dtype=torch.float32, device=dev); Bd[t] = torch.as_tensor(done.astype(np.float32), device=dev)
            Bdec[t] = torch.as_tensor(decide.astype(np.float32), device=dev)
            mgr_timer[decide] = K; mgr_timer = mgr_timer - 1
            ep_r += rew; ep_c += cost
            for n in np.where(done)[0]:
                rs.append(float(info["success"][n])); rc.append(ep_c[n]); ep_r[n] = 0; ep_c[n] = 0
            mgr_timer[done] = 0; obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gs += N
        with torch.no_grad(): last_v = net.value(obs_t.reshape(N, A * O))
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - Bd[t]; nv = last_v if t == T - 1 else Bv[t + 1]; d = Br[t] + gamma * nv * nnt - Bv[t]; g = d + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + Bv).reshape(T * N)
        f_obs = Bo.reshape(T * N, A, O); f_glob = f_obs.reshape(T * N, A * O); f_tk = Btk.reshape(T * N); f_mv = Bmv.reshape(T * N, A)
        f_lpm = Blpm.reshape(T * N); f_lpw = Blpw.reshape(T * N, A); f_dec = Bdec.reshape(T * N)
        fa = adv.reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"]); pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); av = fa[j].unsqueeze(1)
                to = tgt_oh(f_tk[j], len(j), A, centers, dev); wd = net.wdist(f_obs[j], to); nlpw = wd.log_prob(f_mv[j]); rw = torch.exp(nlpw - f_lpw[j])
                plw = -torch.min(rw * av, torch.clamp(rw, 1 - cfg["clip"], 1 + cfg["clip"]) * av).mean()
                dj = j[f_dec[j] > 0.5]
                if dj.numel() > 0:
                    md = net.mdist(f_glob[dj]); nlpm = md.log_prob(f_tk[dj]); rm = torch.exp(nlpm - f_lpm[dj]); avm = fa[dj]
                    plm = -torch.min(rm * avm, torch.clamp(rm, 1 - cfg["clip"], 1 + cfg["clip"]) * avm).mean(); entm = md.entropy().mean()
                else: plm = torch.zeros((), device=dev); entm = torch.zeros((), device=dev)
                vloss = ((net.value(f_glob[j]) - ret[j]) ** 2).mean(); ent = entm + wd.entropy().mean()
                loss = plm + plw + cfg["vf"] * vloss - cfg["ent"] * ent
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                pl += (plm + plw).item(); vl += vloss.item(); en += ent.item(); nu += 1
        tm = lambda x: float(np.mean(x[-300:])) if x else float("nan")
        row = dict(iter=it, level=env.level, steps=gs, success_rate=tm(rs), casualties=tm(rc), safe_choice=tm(rsafe), entropy=en / nu)
        hist.append(row)
        if it % max(1, cfg["iters"] // 25) == 0 or it == cfg["iters"] - 1:
            print(f"it {it:4d} | niv {env.level} | succes {row['success_rate']:.2f} | morts/ep {row['casualties']:.2f} | ent {row['entropy']:.2f} | chef-bon-cote {row['safe_choice']:.2f}")
    with open(os.path.join(rd, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(rd, "model.pt"))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_title("Reussite (v3 chef-arbitre)"); ax[0].set_ylim(-0.05, 1.05); ax[0].axvline(cfg["warmup"], color="gray", ls="--")
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].set_title("Morts / episode"); ax[1].axvline(cfg["warmup"], color="gray", ls="--"); fig.tight_layout(); fig.savefig(os.path.join(rd, "courbes.png")); plt.close(fig)
    except Exception as e: print("courbes:", e)
    if cfg["gif"]: s, c = render_v3(net, dev, os.path.join(rd, "apres.gif"), level=1); print(f"[apres] succes={s} morts={c}")
    idxf = os.path.join(root, "index.csv"); newf = not os.path.exists(idxf)
    with open(idxf, "a", newline="") as f:
        w = csv.writer(f)
        if newf: w.writerow(["run", "iters", "envs", "success_final", "casualties_final", "cas_pen"])
        w.writerow([rid, cfg["iters"], cfg["envs"], f"{hist[-1]['success_rate']:.3f}", f"{hist[-1]['casualties']:.3f}", cfg["cas_pen"]])
    print(f"[fini] reussite={hist[-1]['success_rate']:.2f} morts/ep={hist[-1]['casualties']:.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("iters",1000,int),("warmup",200,int),("envs",512,int),("rollout",32,int),("hidden",64,int),("lr",3e-4,float),("gamma",0.99,float),("gae",0.95,float),("clip",0.2,float),("epochs",4,int),("minibatches",4,int),("vf",0.5,float),("ent",0.01,float),("seed",0,int),("cas_pen",0.5,float),("mgr_period",8,int),("mgr_lr",1e-3,float)]:
        p.add_argument("--"+k.replace("_","-"), default=v, type=t, dest=k)
    p.add_argument("--no-gif", action="store_true")
    a = p.parse_args(); cfg = vars(a); cfg["gif"] = not cfg.pop("no_gif"); train(cfg)
