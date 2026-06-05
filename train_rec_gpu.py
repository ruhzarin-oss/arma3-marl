"""B.1 — MEMOIRE sous occlusion (GPU). Le learner (camp 0) ne voit l'ennemi que dans un rayon (sight) ; il doit
se SOUVENIR d'un ennemi vu puis cache. RecNet (GRU) vs FF (sans memoire), meme tache, adversaires figes aleatoires
(tache stationnaire -> mesure propre). On attend : REC > FF sur le taux de victoire/securisation sous occlusion.
--rnn 1 = GRU, --rnn 0 = FF. Tout sur la 3090."""
import time, argparse, copy
import torch, torch.nn as nn
torch.backends.cudnn.enabled = False
from torch.distributions import Categorical
from koth_gpu import KothGPU


class FF(nn.Module):
    def __init__(self, O, nact, hidden=256):
        super().__init__(); self.hidden = hidden
        self.body = nn.Sequential(nn.Linear(O, hidden), nn.ReLU(), nn.Linear(hidden, hidden), nn.ReLU())
        self.pi = nn.Linear(hidden, nact); self.v = nn.Linear(hidden, 1)
    def step(self, obs, h=None):
        y = self.body(obs); return self.pi(y), self.v(y).squeeze(-1).mean(-1), None
    def seq(self, obs_seq, done_seq):
        y = self.body(obs_seq); return self.pi(y), self.v(y).squeeze(-1).mean(-1)


class RecNet(nn.Module):
    def __init__(self, O, nact, hidden=256):
        super().__init__(); self.hidden = hidden
        self.enc = nn.Sequential(nn.Linear(O, hidden), nn.ReLU())
        self.gru = nn.GRU(hidden, hidden); self.pi = nn.Linear(hidden, nact); self.v = nn.Linear(hidden, 1)
    def step(self, obs, h):  # obs (B,A,O), h (1,B*A,H)
        B, A, O = obs.shape; x = self.enc(obs).reshape(1, B * A, -1)
        y, h2 = self.gru(x, h); y = y.reshape(B, A, -1)
        return self.pi(y), self.v(y).squeeze(-1).mean(-1), h2
    def seq(self, obs_seq, done_seq):  # (T,n,A,O),(T,n) -> logits (T,n,A,nact), val (T,n)
        T, n, A, O = obs_seq.shape; h = torch.zeros(1, n * A, self.hidden, device=obs_seq.device)
        lo = []; va = []
        for t in range(T):
            if t > 0:
                m = (1 - done_seq[t - 1]).reshape(1, n, 1).expand(1, n, A).reshape(1, n * A, 1); h = h * m
            lg, v, h = self.step(obs_seq[t], h); lo.append(lg); va.append(v)
        return torch.stack(lo), torch.stack(va)


def clone_frozen(net, dev):
    f = copy.deepcopy(net).to(dev)
    for p in f.parameters(): p.requires_grad_(False)
    f.eval(); return f


def train(rnn=True, iters=300, envs=8192, rollout=20, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2, epochs=4,
          vf=0.5, ent=0.01, hidden=256, mb_env=2048, sight=45.0, spawn_jit=0.25, hit=0.13, seed=0):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = KothGPU(num_envs=envs, hit=hit, spawn_jit=spawn_jit, sight=sight, occ=True, device=dev, seed=seed)
    C, A, O, NA = env.C, env.A, env.obs_dim, env.n_actions; obs = env.reset(); N = envs; T = rollout
    Cls = RecNet if rnn else FF
    learner = Cls(O, NA, hidden).to(dev); opt = torch.optim.Adam(learner.parameters(), lr=lr)
    opp = [clone_frozen(RecNet(O, NA, hidden).to(dev), dev) for _ in range(2)]  # adversaires figes (aleatoires)
    ot = list(obs); win = torch.zeros((), device=dev); sec = torch.zeros((), device=dev); dec = torch.zeros((), device=dev); donec = torch.zeros((), device=dev)
    gstep = 0; t0 = time.time(); tag = "GRU(memoire)" if rnn else "FF(sans memoire)"
    print("B.1 %s | envs=%d O=%d sight=%.0f" % (tag, N, O, sight), flush=True)
    ho = [torch.zeros(1, N * A, hidden, device=dev) for _ in range(2)]
    for it in range(iters):
        hl = torch.zeros(1, N * A, hidden, device=dev) if rnn else None
        B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                 val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        for t in range(T):
            with torch.no_grad():
                lg, v, hl = learner.step(ot[0], hl); dd = Categorical(logits=lg); a0 = dd.sample()
                B["obs"][t] = ot[0]; B["act"][t] = a0; B["logp"][t] = dd.log_prob(a0); B["val"][t] = v
                a1, ho[0], _ = (lambda r: (Categorical(logits=r[0]).sample(), r[2], None))(opp[0].step(ot[1], ho[0]))
                a2, ho[1], _ = (lambda r: (Categorical(logits=r[0]).sample(), r[2], None))(opp[1].step(ot[2], ho[1]))
            nobs, rews, done, info = env.step([a0, a1, a2])
            B["rew"][t] = rews[0]; B["done"][t] = done
            dm = done.bool(); winner = info["winner"]
            donec += dm.sum(); dec += ((winner >= 0) & dm).sum(); win += ((winner == 0) & dm).sum(); sec += (info["secured"] & dm).sum()
            m = (1 - done).reshape(1, N, 1).expand(1, N, A).reshape(1, N * A, 1)
            if rnn: hl = hl * m
            ho[0] = ho[0] * m; ho[1] = ho[1] * m
            ot = list(nobs); gstep += N
        with torch.no_grad():
            lv = learner.step(ot[0], hl)[1] if rnn else learner.step(ot[0])[1]
        # GAE
        adv = torch.zeros(T, N, device=dev); g = torch.zeros(N, device=dev)
        for t in reversed(range(T)):
            nnt = 1 - B["done"][t]; nv = lv if t == T - 1 else B["val"][t + 1]
            delta = B["rew"][t] + gamma * nv * nnt - B["val"][t]; g = delta + gamma * gae * nnt * g; adv[t] = g
        ret = adv + B["val"]; advn = (adv - adv.mean()) / (adv.std() + 1e-8)
        for _ in range(epochs):
            perm = torch.randperm(N, device=dev)
            for i in range(0, N, mb_env):
                idx = perm[i:i + mb_env]
                logits, vals = learner.seq(B["obs"][:, idx], B["done"][:, idx])
                dist = Categorical(logits=logits); ratio = torch.exp(dist.log_prob(B["act"][:, idx]) - B["logp"][:, idx])
                a_ = advn[:, idx].unsqueeze(2)
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
                vloss = ((vals - ret[:, idx]) ** 2).mean(); e = dist.entropy().mean()
                loss = ploss + vf * vloss - ent * e
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(learner.parameters(), 0.5); opt.step()
        if it % 20 == 0 or it == iters - 1:
            dc = donec.item()
            print("it %4d | %s | learner_win %.2f | securise %.2f | decid %.2f | %.0f tr/s"
                  % (it, tag, (win.item() / dc if dc else 0), (sec.item() / dc if dc else 0), (dec.item() / dc if dc else 0), gstep / (time.time() - t0)), flush=True)
            win.zero_(); sec.zero_(); dec.zero_(); donec.zero_()
    dc = donec.item()
    print("[fini] %s | learner_win %.2f | securise %.2f" % (tag, (win.item() / max(1, dc)), (sec.item() / max(1, dc))), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rnn", type=int, default=1); p.add_argument("--iters", type=int, default=300)
    p.add_argument("--envs", type=int, default=8192); p.add_argument("--rollout", type=int, default=20)
    p.add_argument("--hidden", type=int, default=256); p.add_argument("--mb_env", type=int, default=2048)
    p.add_argument("--sight", type=float, default=45.0); p.add_argument("--hit", type=float, default=0.13)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    train(rnn=bool(a.rnn), iters=a.iters, envs=a.envs, rollout=a.rollout, hidden=a.hidden, mb_env=a.mb_env, sight=a.sight, hit=a.hit, seed=a.seed)
