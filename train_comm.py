"""A2 — COMMUNICATION. Compare une politique AVEC canal de comms vs SANS, sur toy_comm (info distribuee).
Si la comm sert : avec comms >> sans comms. Comm = chaque agent emet un message-vecteur appris,
chacun recoit la MOYENNE des messages des AUTRES (CommNet 1 tour, differentiable). MAPPO."""
import time, argparse
import numpy as np
import torch, torch.nn as nn
from torch.distributions import Categorical
from toy_comm import ToyComm


class CommNet(nn.Module):
    def __init__(self, O, nA, A, h=64, mdim=16, comm=1):
        super().__init__(); self.A = A; self.comm = comm
        self.enc = nn.Sequential(nn.Linear(O, h), nn.Tanh())
        self.msg = nn.Linear(h, mdim)
        self.post = nn.Sequential(nn.Linear(h + mdim, h), nn.Tanh(), nn.Linear(h, nA))
        self.critic = nn.Sequential(nn.Linear(O * A, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))

    def a_logits(self, obs):
        N, A, O = obs.shape
        hh = self.enc(obs)               # (N,A,h)
        m = self.msg(hh)                 # (N,A,mdim)
        if self.comm:
            c = (m.sum(1, keepdim=True) - m) / max(1, A - 1)   # moyenne des messages des AUTRES
        else:
            c = torch.zeros_like(m)
        return self.post(torch.cat([hh, c], dim=-1))

    def value(self, obs):
        N, A, O = obs.shape
        return self.critic(obs.reshape(N, A * O)).squeeze(-1)


def train(comm=1, envs=512, iters=300, rollout=22, lr=3e-4, gamma=0.99, lam=0.95,
          clip=0.2, epochs=4, vf=0.5, ent=0.01, hidden=64, seed=0):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    env = ToyComm(num_envs=envs, seed=seed); obs = env.reset(); N, A, O = obs.shape
    net = CommNet(O, env.n_actions, A, hidden, comm=comm).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr); T = rollout
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    rs = []; gstep = 0; t0 = time.time()
    print("MODE = %s | device=%s" % ("AVEC COMMS" if comm else "SANS COMMS", dev))
    for it in range(iters):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev)
        b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        for t in range(T):
            with torch.no_grad():
                dist = Categorical(logits=net.a_logits(obs_t)); act = dist.sample(); logp = dist.log_prob(act)
                v = net.value(obs_t)
            nobs, rew, done, info = env.step(act.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = act; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew, device=dev); b_done[t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]: rs.append(float(info["success"][n]))
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gstep += N
        with torch.no_grad():
            lastv = net.value(obs_t)
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - b_done[t]; nv = lastv if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + gamma * nv * nnt - b_val[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + b_val).reshape(T * N); adv_n = (adv - adv.mean()) / (adv.std() + 1e-8)
        fo = b_obs.reshape(T * N, A, O); fa = b_act.reshape(T * N, A); fl = b_logp.reshape(T * N, A)
        fad = adv_n.reshape(T * N, 1)
        for _ in range(epochs):
            dist = Categorical(logits=net.a_logits(fo)); nlp = dist.log_prob(fa)
            ratio = torch.exp(nlp - fl)
            ploss = -torch.min(ratio * fad, torch.clamp(ratio, 1 - clip, 1 + clip) * fad).mean()
            vloss = ((net.value(fo) - ret) ** 2).mean(); entropy = dist.entropy().mean()
            loss = ploss + vf * vloss - ent * entropy
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 25 == 0 or it == iters - 1:
            sr = float(np.mean(rs[-1500:])) if rs else float("nan")
            print("it %4d | steps %8d | succes %.2f | %.0f tr/s" % (it, gstep, sr, gstep / (time.time() - t0)))
    sr = float(np.mean(rs[-1500:])) if rs else float("nan")
    print("[fini] %s -> succes final %.2f" % ("AVEC COMMS" if comm else "SANS COMMS", sr))
    return sr


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--comm", type=int, default=1); p.add_argument("--iters", type=int, default=300)
    a = p.parse_args(); train(comm=a.comm, iters=a.iters)
