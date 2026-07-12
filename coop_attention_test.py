"""TEST : l'attention a sa VRAIE place — dans l'ACTEUR, sur une tache qui FORCE la coordination.
Tache CoopNav : A agents doivent couvrir A reperes DISTINCTS (1 chacun) sans se cogner.
  recompense = -somme(distance de chaque repere a l'agent le plus proche) - penalite collisions.
  -> bien faire EXIGE de se repartir : chaque agent doit tenir compte des AUTRES.
3 acteurs, MEME critique central (on ne teste que l'acteur) :
  - AVEUGLE   : own + reperes, ignore les coequipiers (plancher).
  - RESUME    : + centroide des autres (le resume fait-main actuel).
  - ATTENTION : chaque agent PONDERE chaque coequipier (apprend qui regarder).
"""
import sys, time, numpy as np, torch, torch.nn as nn
from torch.distributions import Categorical
DEV = "cuda:0" if torch.cuda.is_available() else "cpu"

class CoopNav:
    def __init__(self, N, A=4, G=10, T=25, collide_pen=0.5, seed=0):
        self.N, self.A, self.G, self.T, self.cp = N, A, G, T, collide_pen
        self.n_actions = 5
        self.moves = torch.tensor([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]], device=DEV).float()
        self.g = torch.Generator(device=DEV); self.g.manual_seed(seed)
        self.obs_dim = 2 + 2 * A          # own pos + A reperes relatifs
    def _rand(self, n):
        return torch.randint(0, self.G, (n, self.A, 2), generator=self.g, device=DEV).float()
    def reset(self):
        self.pos = self._rand(self.N); self.land = self._rand(self.N)
        self.t = torch.zeros(self.N, device=DEV); return self._obs()
    def _obs(self):
        N, A, G = self.N, self.A, self.G
        own = self.pos / G
        land_rel = (self.land[:, None, :, :] - self.pos[:, :, None, :]) / G      # (N,A,L,2)
        own_feat = torch.cat([own, land_rel.reshape(N, A, -1)], dim=2)           # (N,A,2+2A)
        rel = (self.pos[:, None, :, :] - self.pos[:, :, None, :]) / G            # (N,A,A,2) j vu de i
        dist = rel.abs().sum(-1, keepdim=True)
        others = torch.cat([rel, dist], dim=3)                                   # (N,A,A,3) inclut soi (=0)
        return own_feat, others
    def step(self, acts):
        self.pos = (self.pos + self.moves[acts]).clamp(0, self.G - 1)
        dl = (self.land[:, :, None, :] - self.pos[:, None, :, :]).abs().sum(-1)  # (N,L,A)
        mind = dl.min(2).values                                                  # (N,L)
        cov = -mind.sum(1) / self.G
        same = (self.pos[:, :, None, :] == self.pos[:, None, :, :]).all(-1)       # (N,A,A)
        coll = (same.sum(2).float() - 1).clamp(min=0).sum(1) / 2
        rew = cov - self.cp * coll
        self.t += 1; done = self.t >= self.T
        info = {"covered": (mind <= 1).float().mean(1), "coll": coll}
        if done.any():
            m = done; k = int(m.sum())
            self.pos[m] = self._rand(k); self.land[m] = self._rand(k); self.t[m] = 0
        return self._obs(), rew, done, info

class BlindActor(nn.Module):
    def __init__(self, od, na, H=64):
        super().__init__(); self.net = nn.Sequential(nn.Linear(od, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, na))
    def logits(self, of, ot): return self.net(of)

class SummaryActor(nn.Module):
    def __init__(self, od, na, H=64):
        super().__init__(); self.net = nn.Sequential(nn.Linear(od + 3, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, na))
    def logits(self, of, ot):
        N, A, _, _ = ot.shape
        mask = (1 - torch.eye(A, device=ot.device)).view(1, A, A, 1)
        cen = (ot * mask).sum(2) / (A - 1)                                       # centroide des autres
        return self.net(torch.cat([of, cen], dim=2))

class AttnActor(nn.Module):
    def __init__(self, od, na, H=64, heads=4):
        super().__init__()
        self.own = nn.Sequential(nn.Linear(od, H), nn.Tanh())
        self.kv = nn.Linear(3, H)
        self.attn = nn.MultiheadAttention(H, heads, batch_first=True)
        self.head = nn.Sequential(nn.Linear(2 * H, H), nn.Tanh(), nn.Linear(H, na))
    def logits(self, of, ot):
        N, A, _, _ = ot.shape
        q = self.own(of)                                                         # (N,A,H)
        kv = torch.tanh(self.kv(ot))                                             # (N,A,A,H) un jeton par coequipier
        ctx, _ = self.attn(q.reshape(N * A, 1, -1), kv.reshape(N * A, A, -1), kv.reshape(N * A, A, -1))
        return self.head(torch.cat([q, ctx.reshape(N, A, -1)], dim=2))

class Critic(nn.Module):
    def __init__(self, od, H=64):
        super().__init__(); self.net = nn.Sequential(nn.Linear(od, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, 1))
    def value(self, of): return self.net(of).squeeze(-1).mean(-1)

def train(actor_cls, seed=0, iters=300, N=1024, A=4, T=25, lr=3e-4, clip=0.2, epochs=4, mbs=4, gamma=0.99, lam=0.95):
    env = CoopNav(N, A, seed=seed); of, ot = env.reset(); od = env.obs_dim
    torch.manual_seed(seed)
    actor = actor_cls(od, env.n_actions).to(DEV); critic = Critic(od).to(DEV)
    opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=lr)
    OD3 = 3; covers = []
    for it in range(iters):
        b_of = torch.zeros(T, N, A, od, device=DEV); b_ot = torch.zeros(T, N, A, A, OD3, device=DEV)
        b_a = torch.zeros(T, N, A, dtype=torch.long, device=DEV); b_lp = torch.zeros(T, N, A, device=DEV)
        b_v = torch.zeros(T, N, device=DEV); b_r = torch.zeros(T, N, device=DEV); b_d = torch.zeros(T, N, device=DEV)
        ep_cov = []
        for t in range(T):
            with torch.no_grad():
                dist = Categorical(logits=actor.logits(of, ot)); a = dist.sample(); v = critic.value(of)
            (of2, ot2), r, done, info = env.step(a)
            b_of[t] = of; b_ot[t] = ot; b_a[t] = a; b_lp[t] = dist.log_prob(a); b_v[t] = v; b_r[t] = r; b_d[t] = done.float()
            ep_cov.append(info["covered"].mean().item()); of, ot = of2, ot2
        with torch.no_grad(): last_v = critic.value(of)
        adv = torch.zeros(T, N, device=DEV); g = torch.zeros(N, device=DEV)
        for t in reversed(range(T)):
            nnt = 1 - b_d[t]; nv = last_v if t == T - 1 else b_v[t + 1]
            delta = b_r[t] + gamma * nv * nnt - b_v[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + b_v).reshape(T * N)
        fof = b_of.reshape(T * N, A, od); fot = b_ot.reshape(T * N, A, A, OD3)
        fa = b_a.reshape(T * N, A); flp = b_lp.reshape(T * N, A)
        fad = adv.reshape(T * N, 1).expand(T * N, A); fad = (fad - fad.mean()) / (fad.std() + 1e-8)
        idx = np.arange(T * N); mb = (T * N) // mbs
        for _ in range(epochs):
            np.random.shuffle(idx)
            for s in range(0, T * N, mb):
                j = torch.as_tensor(idx[s:s + mb], device=DEV)
                dist = Categorical(logits=actor.logits(fof[j], fot[j]))
                ratio = torch.exp(dist.log_prob(fa[j]) - flp[j]); a_ = fad[j]
                pl = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
                vl = ((critic.value(fof[j]) - ret[j]) ** 2).mean(); ent = dist.entropy().mean()
                loss = pl + 0.5 * vl - 0.01 * ent
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(list(actor.parameters()) + list(critic.parameters()), 0.5); opt.step()
        covers.append(float(np.mean(ep_cov)))
        if it % 50 == 0 or it == iters - 1:
            print("  [%s] it %3d couverture=%.3f" % (actor_cls.__name__, it, covers[-1]), flush=True)
    # eval final : couverture moyenne + collisions sur quelques episodes
    cov_f, coll_f = [], []
    of, ot = env.reset()
    for _ in range(T * 4):
        with torch.no_grad(): a = Categorical(logits=actor.logits(of, ot)).sample()
        (of, ot), r, done, info = env.step(a); cov_f.append(info["covered"].mean().item()); coll_f.append(info["coll"].mean().item())
    return float(np.mean(cov_f[-T:])), float(np.mean(coll_f[-T:]))

if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 8 if SMOKE else 300; SEEDS = [0] if SMOKE else [0, 1, 2]
    print("=== TEST ATTENTION DANS L'ACTEUR (CoopNav) SMOKE=%s ===" % SMOKE, flush=True)
    res = {}
    for cls in [BlindActor, SummaryActor, AttnActor]:
        cov, coll = [], []
        for s in SEEDS:
            c, k = train(cls, seed=s, iters=ITERS); cov.append(c); coll.append(k)
            print("[%s] seed %d -> couverture %.3f collisions %.3f" % (cls.__name__, s, c, k), flush=True)
        res[cls.__name__] = (np.mean(cov), np.std(cov), np.mean(coll), np.std(coll))
    print("\n===== RESULTAT : couverture des reperes (haut=mieux) / collisions (bas=mieux) =====", flush=True)
    print("%-14s | couverture        | collisions" % "acteur", flush=True)
    for k, (cm, cs, km, ks) in res.items():
        print("%-14s | %.3f +/- %.3f    | %.3f +/- %.3f" % (k, cm, cs, km, ks), flush=True)
    print("COOP_TEST_DONE", flush=True)
