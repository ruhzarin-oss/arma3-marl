"""Option 1 — MEMOIRE + COMMUNICATION combinees. Reseau RecComm = encodeur -> canal de comms (CommNet)
-> GRU (memoire) -> action. Interrupteurs --mem / --comm pour les ablations.
toy_both exige les deux : full (mem+comm) doit reussir ; comm-only et mem-only doivent echouer."""
import time, argparse
import numpy as np
import torch, torch.nn as nn
torch.backends.cudnn.enabled = False
from torch.distributions import Categorical
from toy_both import ToyBoth
from toy_macro import ToyMacro


class RecComm(nn.Module):
    def __init__(self, O, nA, A, h=64, g=64, mdim=16, comm=1, mem=1):
        super().__init__(); self.A = A; self.g = g; self.comm = comm; self.mem = mem
        self.enc = nn.Sequential(nn.Linear(O, h), nn.Tanh()); self.msg = nn.Linear(h, mdim)
        ip = h + mdim
        if mem:
            self.a_gru = nn.GRU(ip, g); self.pi = nn.Linear(g, nA)
        else:
            self.post = nn.Sequential(nn.Linear(ip, h), nn.Tanh(), nn.Linear(h, nA))
        self.c_enc = nn.Sequential(nn.Linear(O * A, h), nn.Tanh())
        if mem:
            self.c_gru = nn.GRU(h, g); self.c_v = nn.Linear(g, 1)
        else:
            self.c_v = nn.Sequential(nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))

    def init_h(self, N, dev):
        return (torch.zeros(1, N * self.A, self.g, device=dev), torch.zeros(1, N, self.g, device=dev))

    def a_step(self, obs, ha):
        N, A, O = obs.shape
        hh = self.enc(obs); m = self.msg(hh)
        c = ((m.sum(1, keepdim=True) - m) / max(1, A - 1)) if self.comm else torch.zeros_like(m)
        x = torch.cat([hh, c], -1)
        if self.mem:
            out, ha = self.a_gru(x.reshape(N * A, -1).unsqueeze(0), ha)
            return self.pi(out.squeeze(0)).reshape(N, A, -1), ha
        return self.post(x), ha

    def c_step(self, obs, hc):
        N, A, O = obs.shape
        x = self.c_enc(obs.reshape(N, A * O))
        if self.mem:
            out, hc = self.c_gru(x.unsqueeze(0), hc); return self.c_v(out.squeeze(0)).squeeze(-1), hc
        return self.c_v(x).squeeze(-1), hc


def train(comm=1, mem=1, envs=512, iters=500, env_name='both', rollout=24, lr=3e-4, gamma=0.99, lam=0.95,
          clip=0.2, epochs=4, vf=0.5, ent=0.01, hidden=64, seed=0):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    env = (ToyBoth(num_envs=envs, seed=seed) if env_name=='both' else ToyMacro(num_envs=envs, macro=1, seed=seed)); obs = env.reset(); N, A, O = obs.shape
    net = RecComm(O, env.n_actions, A, hidden, comm=comm, mem=mem).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr); T = rollout
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev); ha, hc = net.init_h(N, dev)
    rs = []; gstep = 0; t0 = time.time()
    tag = ("MEM+COMM (full)" if (mem and comm) else ("COMM seul (sans memoire)" if comm else ("MEMOIRE seule (sans comms)" if mem else "RIEN")))
    print("MODE = %s | device=%s" % (tag, dev))
    for it in range(iters):
        b_obs = torch.zeros(T, N, A, O, device=dev); b_act = torch.zeros(T, N, A, dtype=torch.long, device=dev)
        b_logp = torch.zeros(T, N, A, device=dev); b_rew = torch.zeros(T, N, device=dev)
        b_val = torch.zeros(T, N, device=dev); b_done = torch.zeros(T, N, device=dev)
        ha0 = ha.detach().clone(); hc0 = hc.detach().clone()
        for t in range(T):
            with torch.no_grad():
                logits, ha = net.a_step(obs_t, ha); v, hc = net.c_step(obs_t, hc)
                dist = Categorical(logits=logits); act = dist.sample(); logp = dist.log_prob(act)
            nobs, rew, done, info = env.step(act.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = act; b_logp[t] = logp; b_val[t] = v
            b_rew[t] = torch.as_tensor(rew, device=dev); b_done[t] = torch.as_tensor(done, device=dev)
            for n in np.where(done)[0]: rs.append(float(info["success"][n]))
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
        for _ in range(epochs):
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
            loss = ploss + vf * vloss - ent * entropy
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 40 == 0 or it == iters - 1:
            sr = float(np.mean(rs[-1500:])) if rs else float("nan")
            print("it %4d | steps %8d | succes %.2f | %.0f tr/s" % (it, gstep, sr, gstep / (time.time() - t0)))
    sr = float(np.mean(rs[-1500:])) if rs else float("nan")
    print("[fini] %s -> succes final %.2f" % (tag, sr)); return sr


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--comm", type=int, default=1); p.add_argument("--mem", type=int, default=1); p.add_argument("--iters", type=int, default=500); p.add_argument("--env", default="both")
    a = p.parse_args(); train(comm=a.comm, mem=a.mem, iters=a.iters, env_name=a.env)
