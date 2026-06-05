"""A1 — MEMOIRE. Compare une politique RECURRENTE (GRU) a une politique SANS memoire (feedforward)
sur toy_mem (objectif visible au depart puis cache). Si la memoire sert, la GRU >> la feedforward.
MAPPO : politique partagee + critique central. Version recurrente = BPTT sur le rollout (masquage aux fins d'episode)."""
import time, argparse
import numpy as np
import torch, torch.nn as nn
torch.backends.cudnn.enabled = False
from torch.distributions import Categorical
from toy_mem import ToyMem
from toy_dyn import ToyDyn
from toy_macro import ToyMacro


class FF(nn.Module):
    def __init__(self, O, nA, A, h=64):
        super().__init__(); self.A = A
        self.actor = nn.Sequential(nn.Linear(O, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, nA))
        self.critic = nn.Sequential(nn.Linear(O * A, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))

    def a_logits(self, obs): return self.actor(obs)

    def value(self, obs):
        N, A, O = obs.shape; return self.critic(obs.reshape(N, A * O)).squeeze(-1)


class REC(nn.Module):
    def __init__(self, O, nA, A, h=64, g=64):
        super().__init__(); self.A = A; self.g = g
        self.a_enc = nn.Sequential(nn.Linear(O, h), nn.Tanh()); self.a_gru = nn.GRU(h, g); self.a_pi = nn.Linear(g, nA)
        self.c_enc = nn.Sequential(nn.Linear(O * A, h), nn.Tanh()); self.c_gru = nn.GRU(h, g); self.c_v = nn.Linear(g, 1)

    def init_h(self, N, dev):
        return (torch.zeros(1, N * self.A, self.g, device=dev), torch.zeros(1, N, self.g, device=dev))

    def a_step(self, obs, ha):
        N, A, O = obs.shape
        x = self.a_enc(obs.reshape(N * A, O)).unsqueeze(0)
        out, ha = self.a_gru(x, ha)
        return self.a_pi(out.squeeze(0)).reshape(N, A, -1), ha

    def c_step(self, obs, hc):
        N, A, O = obs.shape
        x = self.c_enc(obs.reshape(N, A * O)).unsqueeze(0)
        out, hc = self.c_gru(x, hc)
        return self.c_v(out.squeeze(0)).squeeze(-1), hc


def train(rnn=1, envs=512, iters=400, env_name='mem', save='', rollout=26, lr=3e-4, gamma=0.99, lam=0.95,
          clip=0.2, epochs=4, vf=0.5, ent=0.01, hidden=64, seed=0):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    env = {'mem': lambda: ToyMem(num_envs=envs, seed=seed), 'dyn': lambda: ToyDyn(num_envs=envs, seed=seed), 'macro': lambda: ToyMacro(num_envs=envs, macro=1, seed=seed), 'prim': lambda: ToyMacro(num_envs=envs, macro=0, seed=seed)}[env_name](); obs = env.reset(); N, A, O = obs.shape
    net = (REC if rnn else FF)(O, env.n_actions, A, hidden).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr); T = rollout
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev)
    if rnn: ha, hc = net.init_h(N, dev)
    rs = []; gstep = 0; t0 = time.time()
    print("MODE = %s | device=%s | N=%d A=%d O=%d" % ("RECURRENT (memoire)" if rnn else "FEEDFORWARD (sans memoire)", dev, N, A, O))
    for it in range(iters):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev)
        b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        if rnn: ha0 = ha.detach().clone(); hc0 = hc.detach().clone()
        for t in range(T):
            with torch.no_grad():
                if rnn:
                    logits, ha = net.a_step(obs_t, ha); v, hc = net.c_step(obs_t, hc)
                else:
                    logits = net.a_logits(obs_t); v = net.value(obs_t)
                dist = Categorical(logits=logits); act = dist.sample(); logp = dist.log_prob(act)
            nobs, rew, done, info = env.step(act.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = act; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew, device=dev); b_done[t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]: rs.append(float(info["success"][n]))
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=dev); gstep += N
            if rnn:
                m = torch.as_tensor(1 - done, dtype=torch.float32, device=dev)
                ha = ha * m.repeat_interleave(A).view(1, N * A, 1); hc = hc * m.view(1, N, 1)
        with torch.no_grad():
            lastv = (net.c_step(obs_t, hc)[0] if rnn else net.value(obs_t))
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - b_done[t]; nv = lastv if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + gamma * nv * nnt - b_val[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
        ret = adv + b_val
        adv_n = (adv - adv.mean()) / (adv.std() + 1e-8)
        for _ in range(epochs):
            if rnn:
                ha_ = ha0.clone(); hc_ = hc0.clone()
                nlp = torch.zeros(T, N, A, device=dev); nent = torch.zeros(T, N, A, device=dev); nval = torch.zeros(T, N, device=dev)
                for t in range(T):
                    logits, ha_ = net.a_step(b_obs[t], ha_); dist = Categorical(logits=logits)
                    nlp[t] = dist.log_prob(b_act[t]); nent[t] = dist.entropy()
                    v, hc_ = net.c_step(b_obs[t], hc_); nval[t] = v
                    m = (1 - b_done[t])
                    ha_ = ha_ * m.repeat_interleave(A).view(1, N * A, 1); hc_ = hc_ * m.view(1, N, 1)
                ratio = torch.exp(nlp - b_logp); a_ = adv_n.unsqueeze(-1)
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
                vloss = ((nval - ret) ** 2).mean(); entropy = nent.mean()
            else:
                fo = b_obs.reshape(T * N, A, O); fa = b_act.reshape(T * N, A); fl = b_logp.reshape(T * N, A)
                dist = Categorical(logits=net.a_logits(fo)); nlp = dist.log_prob(fa)
                ratio = torch.exp(nlp - fl); a_ = adv_n.reshape(T * N, 1)
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
                vloss = ((net.value(fo) - ret.reshape(T * N)) ** 2).mean(); entropy = dist.entropy().mean()
            loss = ploss + vf * vloss - ent * entropy
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 25 == 0 or it == iters - 1:
            sr = float(np.mean(rs[-1500:])) if rs else float("nan")
            print("it %4d | steps %8d | succes %.2f | %.0f tr/s" % (it, gstep, sr, gstep / (time.time() - t0)))
    sr = float(np.mean(rs[-1500:])) if rs else float("nan")
    if save:
        torch.save(net.state_dict(), save); print("modele sauve ->", save)
    print("[fini] %s -> succes final %.2f" % ("RECURRENT" if rnn else "FEEDFORWARD", sr))
    return sr


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rnn", type=int, default=1); p.add_argument("--iters", type=int, default=400); p.add_argument("--env", default="mem"); p.add_argument("--save", default="")
    a = p.parse_args(); train(rnn=a.rnn, iters=a.iters, env_name=a.env, save=a.save)
