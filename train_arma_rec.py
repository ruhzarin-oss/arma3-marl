"""Option 2 — fine-tune RECURRENT (memoire) du combat dynamique DANS ARMA (B1, vraie IA mobile),
multi-serveurs. Boucle PPO-BPTT (de train_mem) + MultiArmaEnv(env_b1=1). Warm-start depuis une
politique toy_dyn recurrente (--init pretrain_dyn_rec.pt). Sauve modele + history."""
import time, argparse, os, csv
import numpy as np
import torch, torch.nn as nn
torch.backends.cudnn.enabled = False
from datetime import datetime
from torch.distributions import Categorical
from train_mem import REC
from arma_env_multi import MultiArmaEnv
from train_harmattan import desktop_root


def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements")
    rid = "run_armarec_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(root, rid); os.makedirs(run_dir, exist_ok=True)
    print("[run arma-rec] %s | device=%s" % (run_dir, dev))
    env = MultiArmaEnv(num_servers=cfg["servers"], per_server=cfg["envs"], max_steps=cfg["max_steps"],
                       step_wait=cfg["step_wait"], settle=cfg["settle"], spacing=cfg["spacing"], acc=4.0, env_b1=(0 if cfg.get("macro") else 1), env_macro=cfg.get("macro", 0))
    obs = env.reset(); N, A, O = obs.shape
    print("env pret: N=%d A=%d O=%d" % (N, A, O))
    net = REC(O, env.n_actions, A, cfg["hidden"]).to(dev)
    if cfg["init"]:
        net.load_state_dict(torch.load(cfg["init"], map_location=dev)); print("WARM-START recurrent depuis", cfg["init"])
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"]); T = cfg["rollout"]
    gamma, lam, cp, clip = cfg["gamma"], cfg["gae"], cfg["cas_pen"], cfg["clip"]
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev); ha, hc = net.init_h(N, dev)
    ep_ret = np.zeros(N); ep_cas = np.zeros(N); rs = []; rc = []; gstep = 0; hist = []; t0 = time.time()
    for it in range(cfg["iters"]):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev)
        b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        ha0 = ha.detach().clone(); hc0 = hc.detach().clone()
        for t in range(T):
            with torch.no_grad():
                logits, ha = net.a_step(obs_t, ha); v, hc = net.c_step(obs_t, hc)
                dist = Categorical(logits=logits); act = dist.sample(); logp = dist.log_prob(act)
            nobs, rew, cost, done, info = env.step(act.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = act; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew - cp * cost, dtype=torch.float32, device=dev)
            b_done[t] = torch.as_tensor(done, dtype=torch.float32, device=dev)
            ep_ret += rew; ep_cas += cost
            for n in np.where(done)[0]:
                rs.append(float(info["success"][n])); rc.append(ep_cas[n]); ep_ret[n] = 0; ep_cas[n] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gstep += N
            m = torch.as_tensor(1 - done, dtype=torch.float32, device=dev)
            ha = ha * m.repeat_interleave(A).view(1, N * A, 1); hc = hc * m.view(1, N, 1)
        with torch.no_grad():
            lastv = net.c_step(obs_t, hc)[0]
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - b_done[t]; nv = lastv if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + gamma * nv * nnt - b_val[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
        ret = adv + b_val; adv_n = (adv - adv.mean()) / (adv.std() + 1e-8)
        pl = vl = en = 0.0; nu = 0
        for _ in range(cfg["epochs"]):
            ha_ = ha0.clone(); hc_ = hc0.clone()
            nlp = torch.zeros(T, N, A, device=dev); nent = torch.zeros(T, N, A, device=dev); nval = torch.zeros(T, N, device=dev)
            for t in range(T):
                logits, ha_ = net.a_step(b_obs[t], ha_); dist = Categorical(logits=logits)
                nlp[t] = dist.log_prob(b_act[t]); nent[t] = dist.entropy()
                v, hc_ = net.c_step(b_obs[t], hc_); nval[t] = v
                m = (1 - b_done[t]); ha_ = ha_ * m.repeat_interleave(A).view(1, N * A, 1); hc_ = hc_ * m.view(1, N, 1)
            ratio = torch.exp(nlp - b_logp); a_ = adv_n.unsqueeze(-1)
            ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
            vloss = ((nval - ret) ** 2).mean(); entropy = nent.mean()
            loss = ploss + cfg["vf"] * vloss - cfg["ent"] * entropy
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
            pl += ploss.item(); vl += vloss.item(); en += entropy.item(); nu += 1
        tm = lambda x: float(np.mean(x[-200:])) if x else float("nan")
        el = time.time() - t0
        row = dict(iter=it, steps=gstep, success_rate=tm(rs), casualties=tm(rc), entropy=en / nu, tps=gstep / el)
        hist.append(row)
        print("it %4d | steps %7d | succes %.2f | morts/ep %.2f | ent %.2f | %.1f tr/s | %.0fs"
              % (it, gstep, row["success_rate"], row["casualties"], row["entropy"], row["tps"], el))
        if it % 10 == 0 or it == cfg["iters"] - 1:
            torch.save(net.state_dict(), os.path.join(run_dir, "model.pt"))
            with open(os.path.join(run_dir, "history.csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(hist[0].keys())); w.writeheader(); w.writerows(hist)
    torch.save(net.state_dict(), os.path.join(run_dir, "model.pt"))
    print("[fini] %s | reussite=%.2f" % (run_dir, hist[-1]["success_rate"]))
    return run_dir


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("servers", 8, int), ("envs", 8, int), ("iters", 80, int), ("rollout", 16, int),
                    ("max_steps", 22, int), ("hidden", 64, int), ("lr", 3e-4, float), ("gamma", 0.99, float),
                    ("gae", 0.95, float), ("clip", 0.2, float), ("epochs", 4, int), ("vf", 0.5, float),
                    ("ent", 0.02, float), ("cas_pen", 0.3, float), ("step_wait", 2.4, float),
                    ("settle", 0.6, float), ("spacing", 450, int)]:
        p.add_argument("--" + k.replace("_", "-"), default=v, type=t, dest=k)
    p.add_argument("--init", default=""); p.add_argument("--macro", type=int, default=0)
    a = p.parse_args(); train(vars(a))
