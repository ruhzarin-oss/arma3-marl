"""Étape 3 variante — c VARIABLE (bouton de risque). La politique est conditionnée sur c (tiré
dans {0.1..0.5} par épisode) ; un λ par valeur de c (montée-descente duale). À l'éval, on règle c
à volonté et on vérifie que le comportement s'adapte (pertes qui suivent le bouton)."""
import os, json, argparse
import numpy as np, torch, torch.nn as nn
from datetime import datetime
from toy2d_v1 import VectorizedToy2Dv1
from train_harmattan import ActorCritic, desktop_root
C_VALS = np.array([0.1, 0.2, 0.3, 0.4, 0.5]); CMAX = 0.5

def aug(obs_t, c_env, dev):
    N, A, O = obs_t.shape
    ca = torch.as_tensor(c_env / CMAX, dtype=torch.float32, device=dev)[:, None, None].expand(N, A, 1)
    return torch.cat([obs_t, ca], -1)
def bin_of(c_env): return np.argmin(np.abs(C_VALS[None, :] - c_env[:, None]), axis=1)

def evaluate_at(net, dev, c, p_hit, n=256, seed=123):
    env = VectorizedToy2Dv1(num_envs=n, p_hit=p_hit, seed=seed); obs = env.reset()
    c_env = np.full(n, c, dtype=np.float32); succ, cas = [], []; epc = np.zeros(n)
    for _ in range(300):
        o = aug(torch.as_tensor(obs, dtype=torch.float32, device=dev), c_env, dev)
        with torch.no_grad(): a = net.actor(o).argmax(-1).cpu().numpy()
        obs, rew, cost, done, info = env.step(a); epc += cost
        for m in np.where(done)[0]:
            succ.append(float(info["success"][m])); cas.append(epc[m]); epc[m] = 0
    return (float(np.mean(succ)) if succ else float("nan"), float(np.mean(cas)) if cas else float("nan"))

def train(cfg):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    root = os.path.join(desktop_root(), "Harmattan-entrainements"); rid = datetime.now().strftime("run_cmdpvar_%Y%m%d_%H%M%S"); rd = os.path.join(root, rid); os.makedirs(rd, exist_ok=True)
    json.dump(cfg, open(os.path.join(rd, "config.json"), "w"), indent=2); print(f"[run CMDP-var] {rd} | {dev} | c in {list(C_VALS)} p_hit={cfg['p_hit']}")
    env = VectorizedToy2Dv1(num_envs=cfg["envs"], p_hit=cfg["p_hit"], seed=cfg["seed"]); obs = env.reset(); N, A, O = obs.shape; O1 = O + 1
    net = ActorCritic(O1, env.n_actions, A, cfg["hidden"]).to(dev); opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    lam = np.full(len(C_VALS), cfg["lambda0"]); rng = np.random.default_rng(0); c_env = C_VALS[rng.integers(0, len(C_VALS), N)].astype(np.float32)
    T, gamma, gae = cfg["rollout"], cfg["gamma"], cfg["gae"]; obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    epc = np.zeros(N); rs = []; rcb = [[] for _ in C_VALS]; gs = 0
    for it in range(cfg["iters"]):
        b_obs = torch.zeros(T, N, A, O1, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev); b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        for t in range(T):
            oaug = aug(obs_t, c_env, dev)
            with torch.no_grad(): a, logp = net.act(oaug); v = net.value(oaug)
            nobs, rew, cost, done, info = env.step(a.cpu().numpy()); bins = bin_of(c_env)
            b_obs[t] = oaug; b_act[t] = a; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew - lam[bins] * cost, dtype=torch.float32, device=dev); b_done[t] = torch.as_tensor(done.astype(np.float32), device=dev)
            epc += cost
            for m in np.where(done)[0]:
                rs.append(float(info["success"][m])); rcb[bins[m]].append(epc[m]); epc[m] = 0; c_env[m] = C_VALS[rng.integers(0, len(C_VALS))]
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gs += N
        with torch.no_grad(): last_v = net.value(aug(obs_t, c_env, dev))
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - b_done[t]; nv = last_v if t == T - 1 else b_val[t + 1]; d = b_rew[t] + gamma * nv * nnt - b_val[t]; g = d + gamma * gae * nnt * g; adv[t] = g
        ret = (adv + b_val).reshape(T * N); f_obs = b_obs.reshape(T * N, A, O1); f_act = b_act.reshape(T * N, A); f_logp = b_logp.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8); f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"])
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); o = f_obs[j]
                nlp, ent = net.evaluate(o, f_act[j]); ratio = torch.exp(nlp - f_logp[j]); a_ = f_adv[j]
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
                vloss = ((net.value(o) - ret[j]) ** 2).mean(); loss = ploss + cfg["vf"] * vloss - cfg["ent"] * ent.mean()
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        for bi in range(len(C_VALS)):
            if rcb[bi]: lam[bi] = float(np.clip(lam[bi] + cfg["lambda_lr"] * (float(np.mean(rcb[bi][-200:])) - C_VALS[bi]), 0, cfg["lambda_max"]))
        if it % max(1, cfg["iters"] // 12) == 0 or it == cfg["iters"] - 1:
            sr = float(np.mean(rs[-500:])) if rs else float("nan")
            print(f"it {it:4d} | succes {sr:.2f} | lambda[.1->.5]=[" + ",".join(f"{x:.1f}" for x in lam) + "]")
    torch.save(net.state_dict(), os.path.join(rd, "model.pt"))
    print("=== EVAL : on tourne le BOUTON DE RISQUE ===")
    for c in [0.1, 0.3, 0.5]:
        s, k = evaluate_at(net, dev, c, cfg["p_hit"]); print(f"  c={c} -> reussite {s:.2f} | pertes/ep {k:.2f}")
    print("[fini]")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k, v, t in [("iters",700,int),("envs",512,int),("rollout",32,int),("hidden",64,int),("lr",3e-4,float),("gamma",0.99,float),("gae",0.95,float),("clip",0.2,float),("epochs",4,int),("minibatches",4,int),("vf",0.5,float),("ent",0.01,float),("seed",0,int),("p_hit",0.4,float),("lambda0",1.0,float),("lambda_lr",0.1,float),("lambda_max",10.0,float)]:
        p.add_argument("--"+k.replace("_","-"), default=v, type=t, dest=k)
    a = p.parse_args(); train(vars(a))
