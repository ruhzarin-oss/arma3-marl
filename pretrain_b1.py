"""Pre-entrainement RAPIDE sur toy_b1 (NumPy, obs calee sur Arma B1) -> poids transferables vers Arma B1.
MAPPO (politique partagee + critique central), scalarisation reward - cas_pen*cost. Sauve pretrain_b1.pt."""
import time, argparse
import numpy as np
import torch, torch.nn as nn
from toy_b1 import ToyB1
from train_harmattan import ActorCritic


def pretrain(envs=4096, iters=800, rollout=24, hidden=64, lr=3e-4, gamma=0.99, gae=0.95,
             clip=0.2, epochs=4, minibatches=8, vf=0.5, ent=0.01, cas_pen=0.4, seed=0,
             out="/home/younes/arma3-marl/pretrain_b1.pt"):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    env = ToyB1(num_envs=envs, seed=seed); obs = env.reset(); N, A, O = obs.shape
    net = ActorCritic(O, env.n_actions, A, hidden).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    ep_ret = np.zeros(N); ep_cas = np.zeros(N); rs = []; rc = []; gstep = 0; t0 = time.time(); T = rollout
    print("pretrain toy_b1 | device=%s | N=%d A=%d O=%d" % (dev, N, A, O))
    for it in range(iters):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev)
        b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        for t in range(T):
            with torch.no_grad():
                aa, logp = net.act(obs_t); v = net.value(obs_t)
            nobs, rew, cost, done, info = env.step(aa.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = aa; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew - cas_pen * cost, dtype=torch.float32, device=dev)
            b_done[t] = torch.as_tensor(done, device=dev)
            ep_ret += rew; ep_cas += cost
            for k in np.where(done)[0]:
                rs.append(float(info["success"][k])); rc.append(ep_cas[k]); ep_ret[k] = 0; ep_cas[k] = 0
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gstep += N
        with torch.no_grad():
            last_v = net.value(obs_t)
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1.0 - b_done[t]; nv = last_v if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + gamma * nv * nnt - b_val[t]; g = delta + gamma * gae * nnt * g; adv[t] = g
        ret = (adv + b_val).reshape(T * N)
        f_obs = b_obs.reshape(T * N, A, O); f_act = b_act.reshape(T * N, A); f_logp = b_logp.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8); f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // minibatches)
        for _ in range(epochs):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=dev); o = f_obs[j]
                nlp, et = net.evaluate(o, f_act[j]); ratio = torch.exp(nlp - f_logp[j]); a_ = f_adv[j]
                pl = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
                vl = ((net.value(o) - ret[j]) ** 2).mean()
                loss = pl + vf * vl - ent * et.mean()
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 40 == 0 or it == iters - 1:
            sr = float(np.mean(rs[-800:])) if rs else float("nan")
            cc = float(np.mean(rc[-800:])) if rc else float("nan")
            print("it %4d | steps %9d | succes %.2f | morts/ep %.2f | %.0f tr/s" % (it, gstep, sr, cc, gstep / (time.time() - t0)))
    torch.save(net.state_dict(), out)
    print("[fini] modele pre-entraine ->", out)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=800); p.add_argument("--envs", type=int, default=4096)
    p.add_argument("--cas-pen", type=float, default=0.4, dest="cas_pen")
    a = p.parse_args(); pretrain(envs=a.envs, iters=a.iters, cas_pen=a.cas_pen)
