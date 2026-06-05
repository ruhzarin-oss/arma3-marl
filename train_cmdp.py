"""Harmattan Étape 3 — CMDP / Lagrangien. Maximiser la mission SOUS CONTRAINTE de pertes <= c,
via un curseur λ auto-réglé (montée-descente duale). Base v1 (squad à rôles).
Récompense d'entraînement = R_mission - λ * pertes ; mise à jour : λ <- clip(λ + λlr*(pertes_mesurées - c), 0, λmax)."""
import os, json, csv, argparse
import numpy as np, torch, torch.nn as nn
from datetime import datetime
from toy2d_v1 import VectorizedToy2Dv1
from train_harmattan import ActorCritic, desktop_root
from train_harmattan_v1 import render_gif_v1

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements"); rid = datetime.now().strftime("run_cmdp_%Y%m%d_%H%M%S"); rd = os.path.join(root, rid); os.makedirs(rd, exist_ok=True)
    json.dump(cfg, open(os.path.join(rd, "config.json"), "w"), indent=2)
    print(f"[run CMDP] {rd} | {dev} | seuil pertes c={cfg['cost_limit']} p_hit={cfg['p_hit']}")
    env = VectorizedToy2Dv1(num_envs=cfg["envs"], p_hit=cfg["p_hit"], seed=cfg["seed"]); obs = env.reset(); N, A, O = obs.shape
    net = ActorCritic(O, env.n_actions, A, cfg["hidden"]).to(dev); opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    lam = float(cfg["lambda0"]); c = cfg["cost_limit"]
    if cfg["gif"]: s, k = render_gif_v1(net, dev, os.path.join(rd, "avant.gif")); print(f"[avant] succes={s} morts={k}")
    T, gamma, gae = cfg["rollout"], cfg["gamma"], cfg["gae"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    ep_r = np.zeros(N); ep_c = np.zeros(N); rs, rc = [], []; gs = 0; hist = []
    tm = lambda x: float(np.mean(x[-300:])) if x else float("nan")
    for it in range(cfg["iters"]):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev); b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        for t in range(T):
            with torch.no_grad(): a, logp = net.act(obs_t); v = net.value(obs_t)
            nobs, rew, cost, done, info = env.step(a.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = a; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew - lam * cost, dtype=torch.float32, device=dev); b_done[t] = torch.as_tensor(done.astype(np.float32), device=dev)
            ep_r += rew; ep_c += cost
            for n in np.where(done)[0]:
                rs.append(float(info["success"][n])); rc.append(ep_c[n]); ep_r[n] = 0; ep_c[n] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gs += N
        with torch.no_grad(): last_v = net.value(obs_t)
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - b_done[t]; nv = last_v if t == T - 1 else b_val[t + 1]; d = b_rew[t] + gamma * nv * nnt - b_val[t]; g = d + gamma * gae * nnt * g; adv[t] = g
        ret = (adv + b_val).reshape(T * N); f_obs = b_obs.reshape(T * N, A, O); f_act = b_act.reshape(T * N, A); f_logp = b_logp.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8); f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"]); pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); o = f_obs[j]
                nlp, ent = net.evaluate(o, f_act[j]); ratio = torch.exp(nlp - f_logp[j]); a_ = f_adv[j]
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
                vloss = ((net.value(o) - ret[j]) ** 2).mean(); entropy = ent.mean(); loss = ploss + cfg["vf"] * vloss - cfg["ent"] * entropy
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                pl += ploss.item(); vl += vloss.item(); en += entropy.item(); nu += 1
        Chat = tm(rc)  # pertes/épisode mesurées
        if not np.isnan(Chat): lam = float(np.clip(lam + cfg["lambda_lr"] * (Chat - c), 0.0, cfg["lambda_max"]))
        row = dict(iter=it, steps=gs, success_rate=tm(rs), casualties=Chat, lam=lam, cost_limit=c, entropy=en / nu); hist.append(row)
        if it % max(1, cfg["iters"] // 20) == 0 or it == cfg["iters"] - 1:
            print(f"it {it:4d} | succes {row['success_rate']:.2f} | pertes/ep {Chat:.2f} (seuil {c}) | lambda {lam:.2f} | ent {row['entropy']:.2f}")
    with open(os.path.join(rd, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(rd, "model.pt"))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_title("Reussite"); ax[0].set_ylim(-0.05, 1.05)
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].axhline(c, color="black", ls="--", label=f"seuil c={c}"); ax[1].set_title("Pertes/ep vs seuil"); ax[1].legend()
        ax[2].plot(its, [h["lam"] for h in hist], color="purple"); ax[2].set_title("lambda (prix du risque)")
        fig.tight_layout(); fig.savefig(os.path.join(rd, "courbes.png")); plt.close(fig)
    except Exception as e: print("courbes:", e)
    if cfg["gif"]: s, k = render_gif_v1(net, dev, os.path.join(rd, "apres.gif")); print(f"[apres] succes={s} morts={k}")
    print(f"[fini] reussite={hist[-1]['success_rate']:.2f} pertes/ep={hist[-1]['casualties']:.2f} (seuil {c}) lambda={hist[-1]['lam']:.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("iters",600,int),("envs",512,int),("rollout",32,int),("hidden",64,int),("lr",3e-4,float),("gamma",0.99,float),("gae",0.95,float),("clip",0.2,float),("epochs",4,int),("minibatches",4,int),("vf",0.5,float),("ent",0.01,float),("seed",0,int),("p_hit",0.35,float),("cost_limit",0.2,float),("lambda0",0.5,float),("lambda_lr",0.1,float),("lambda_max",10.0,float)]:
        p.add_argument("--"+k.replace("_","-"), default=v, type=t, dest=k)
    p.add_argument("--no-gif", action="store_true")
    a = p.parse_args(); cfg = vars(a); cfg["gif"] = not cfg.pop("no_gif"); train(cfg)
