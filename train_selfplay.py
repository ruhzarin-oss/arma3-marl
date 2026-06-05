"""B2 — SELF-PLAY. Deux politiques (BLUFOR + OPFOR) entrainees SIMULTANEMENT l'une contre l'autre sur toy_selfplay.
Chaque camp = MAPPO feedforward, recompense symetrique (+1 victoire / -1 defaite). On suit la COURSE A L'ARMEMENT :
les taux de victoire des deux camps doivent s'EQUILIBRER (co-adaptation) au lieu d'un camp qui ecrase."""
import time, argparse
import numpy as np
import torch, torch.nn as nn
from torch.distributions import Categorical
from toy_selfplay import ToySelfPlay
from train_mem import FF


def ppo_update(net, opt, b_obs, b_act, b_logp, b_rew, b_val, b_done, lastv, cfg, dev):
    T, N = b_rew.shape
    adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
    gamma, lam = cfg["gamma"], cfg["gae"]
    for t in reversed(range(T)):
        nnt = 1 - b_done[t]; nv = lastv if t == T - 1 else b_val[t + 1]
        delta = b_rew[t] + gamma * nv * nnt - b_val[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
    ret = (adv + b_val).reshape(T * N); adv_n = (adv - adv.mean()) / (adv.std() + 1e-8)
    A = b_act.shape[2]; O = b_obs.shape[3]
    fo = b_obs.reshape(T * N, A, O); fa = b_act.reshape(T * N, A); fl = b_logp.reshape(T * N, A); fad = adv_n.reshape(T * N, 1)
    for _ in range(cfg["epochs"]):
        dist = Categorical(logits=net.a_logits(fo)); nlp = dist.log_prob(fa); ratio = torch.exp(nlp - fl)
        ploss = -torch.min(ratio * fad, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * fad).mean()
        vloss = ((net.value(fo) - ret) ** 2).mean(); entropy = dist.entropy().mean()
        loss = ploss + cfg["vf"] * vloss - cfg["ent"] * entropy
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()


def train(iters=400, envs=512, rollout=24, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=64, hit=0.16, secn=2, seed=0):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = ToySelfPlay(num_envs=envs, hit=hit, secure_n=secn, seed=seed); o0, o1 = env.reset(); N, A, O = o0.shape
    net0 = FF(O, env.n_actions, A, hidden).to(dev); net1 = FF(O, env.n_actions, A, hidden).to(dev)
    opt0 = torch.optim.Adam(net0.parameters(), lr=lr); opt1 = torch.optim.Adam(net1.parameters(), lr=lr)
    T = rollout; o0t = torch.as_tensor(o0, dtype=torch.float32, device=dev); o1t = torch.as_tensor(o1, dtype=torch.float32, device=dev)
    w0 = []; w1 = []; dec = []; gstep = 0; t0 = time.time()
    print("SELF-PLAY | device=%s | N=%d A=%d O=%d" % (dev, N, A, O))
    for it in range(iters):
        B = {s: dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                     logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                     val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev)) for s in (0, 1)}
        for t in range(T):
            with torch.no_grad():
                d0 = Categorical(logits=net0.a_logits(o0t)); a0 = d0.sample(); lp0 = d0.log_prob(a0); v0 = net0.value(o0t)
                d1 = Categorical(logits=net1.a_logits(o1t)); a1 = d1.sample(); lp1 = d1.log_prob(a1); v1 = net1.value(o1t)
            no0, no1, r0, r1, done, info = env.step(a0.cpu().numpy(), a1.cpu().numpy())
            for s, (obs_t, a, lp, v, r) in ((0, (o0t, a0, lp0, v0, r0)), (1, (o1t, a1, lp1, v1, r1))):
                B[s]["obs"][t] = obs_t; B[s]["act"][t] = a; B[s]["logp"][t] = lp; B[s]["val"][t] = v
                B[s]["rew"][t] = torch.as_tensor(r, device=dev); B[s]["done"][t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]:
                if info["decided"][n]:
                    w0.append(float(info["win0"][n])); w1.append(float(info["win1"][n])); dec.append(1.0)
                else:
                    dec.append(0.0)
            o0t = torch.as_tensor(no0, dtype=torch.float32, device=dev); o1t = torch.as_tensor(no1, dtype=torch.float32, device=dev); gstep += N
        with torch.no_grad():
            lv0 = net0.value(o0t); lv1 = net1.value(o1t)
        ppo_update(net0, opt0, B[0]["obs"], B[0]["act"], B[0]["logp"], B[0]["rew"], B[0]["val"], B[0]["done"], lv0, cfg, dev)
        ppo_update(net1, opt1, B[1]["obs"], B[1]["act"], B[1]["logp"], B[1]["rew"], B[1]["val"], B[1]["done"], lv1, cfg, dev)
        if it % 25 == 0 or it == iters - 1:
            tm = lambda x: float(np.mean(x[-2000:])) if x else 0.0
            print("it %4d | BLU victoires %.2f | OPF victoires %.2f | parties decidees %.2f | %.0f tr/s"
                  % (it, tm(w0), tm(w1), tm(dec), gstep / (time.time() - t0)))
    tm = lambda x: float(np.mean(x[-2000:])) if x else 0.0
    dr = tm(dec); print("[fini] BLU %.2f | OPF %.2f | decidees %.2f" % (tm(w0), tm(w1), dr))
    torch.save(net0.state_dict(), "/home/younes/arma3-marl/selfplay_blu.pt")
    torch.save(net1.state_dict(), "/home/younes/arma3-marl/selfplay_opf.pt")
    return tm(w0), tm(w1), dr


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=400)
    a = p.parse_args(); train(iters=a.iters)
