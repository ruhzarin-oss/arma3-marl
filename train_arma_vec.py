"""Entrainement MARL DIRECTEMENT dans Arma 3 (env vectorise ArmaVecEnv).
MAPPO : politique partagee + critique central ; scalarisation reward - cas_pen*cost.
Checkpoints + history.csv + courbes.png dans ~/Bureau/Harmattan-entrainements/run_arma_*."""
import os, json, csv, time, argparse
import numpy as np
import torch, torch.nn as nn
from datetime import datetime
from arma_env_vec import ArmaVecEnv
from train_harmattan import ActorCritic, desktop_root


def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements")
    rid = "run_arma_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(root, rid); os.makedirs(run_dir, exist_ok=True)
    json.dump(cfg, open(os.path.join(run_dir, "config.json"), "w"), indent=2)
    print("[run arma] %s | device=%s" % (run_dir, dev))
    if cfg.get("servers", 1) > 1:
        from arma_env_multi import MultiArmaEnv
        env = MultiArmaEnv(num_servers=cfg["servers"], per_server=cfg["envs"], max_steps=cfg["max_steps"],
                           step_wait=cfg["step_wait"], settle=cfg["settle"], spacing=cfg["spacing"], acc=cfg["acc"], env_b1=cfg.get("b1", 0))
    else:
        env = ArmaVecEnv(num_envs=cfg["envs"], max_steps=cfg["max_steps"], step_wait=cfg["step_wait"],
                         settle=cfg["settle"], spacing=cfg["spacing"], acc=cfg["acc"], seed=cfg["seed"])
    obs = env.reset(); N, A, O = obs.shape
    print("env pret: N=%d A=%d O=%d" % (N, A, O))
    net = ActorCritic(O, env.n_actions, A, cfg["hidden"]).to(dev)
    if cfg.get("init"):
        net.load_state_dict(torch.load(cfg["init"], map_location=dev)); print("WARM-START depuis", cfg["init"])
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    T, gamma, lam, cp = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    ep_ret = np.zeros(N); ep_cas = np.zeros(N); rs, rc, rr = [], [], []; gstep = 0; hist = []
    t0 = time.time()
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
            b_done[t] = torch.as_tensor(done, dtype=torch.float32, device=dev)
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
        tm = lambda x: float(np.mean(x[-200:])) if x else float("nan")
        el = time.time() - t0; tps = gstep / el
        row = dict(iter=it, steps=gstep, success_rate=tm(rs), casualties=tm(rc), ep_return=tm(rr),
                   ploss=pl / nu, vloss=vl / nu, entropy=en / nu, tps=tps)
        hist.append(row)
        print("it %4d | steps %7d | succes %.2f | morts/ep %.2f | retour %+.2f | ent %.2f | %.1f tr/s | %.0fs"
              % (it, gstep, row["success_rate"], row["casualties"], row["ep_return"], row["entropy"], tps, el))
        if it % 10 == 0 or it == cfg["iters"] - 1:
            torch.save(net.state_dict(), os.path.join(run_dir, "model.pt"))
            with open(os.path.join(run_dir, "history.csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(run_dir, "model.pt"))
    with open(os.path.join(run_dir, "history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        its = [h["iter"] for h in hist]; fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(its, [h["success_rate"] for h in hist], color="green"); ax[0].set_ylim(-0.05, 1.05); ax[0].set_title("Reussite (entraine DANS Arma)"); ax[0].set_xlabel("iteration")
        ax[1].plot(its, [h["casualties"] for h in hist], color="red"); ax[1].set_title("Morts / episode"); ax[1].set_xlabel("iteration")
        fig.tight_layout(); fig.savefig(os.path.join(run_dir, "courbes.png")); plt.close(fig)
    except Exception as e:
        print("courbes:", e)
    print("[fini] %s | reussite=%.2f | morts/ep=%.2f" % (run_dir, hist[-1]["success_rate"], hist[-1]["casualties"]))
    return run_dir


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("envs", 64, int), ("iters", 150, int), ("rollout", 24, int), ("max_steps", 18, int),
                    ("hidden", 64, int), ("lr", 3e-4, float), ("gamma", 0.99, float), ("gae", 0.95, float),
                    ("clip", 0.2, float), ("epochs", 4, int), ("minibatches", 4, int), ("vf", 0.5, float),
                    ("ent", 0.01, float), ("seed", 0, int), ("cas_pen", 0.5, float),
                    ("step_wait", 0.5, float), ("settle", 0.4, float), ("spacing", 300, int), ("acc", 4.0, float), ("servers", 1, int), ("b1", 0, int)]:
        p.add_argument("--" + k.replace("_", "-"), default=v, type=t, dest=k)
    p.add_argument("--init", default="", type=str)
    a = p.parse_args(); train(vars(a))
