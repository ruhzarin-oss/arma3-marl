"""MISSION #1 de la batterie — CoverHold (« occuper-tenir »).
Tache : A agents doivent COUVRIR le terrain (etre pres de P points de controle repartis sur la carte)
SANS s'isoler (un agent trop loin de son plus proche coequipier est penalise).
  recompense = couverture_terrain  -  iso_pen * isolement
La TENSION (idee de Younes) : s'etaler pour couvrir (courage) MAIS rester connecte (ne pas s'isoler).
Un agent qui s'agglutine -> couverture faible ; qui se disperse betement -> penalite isolement.
Seule une DISPERSION EQUILIBREE gagne -> exige de lire TOUS les coequipiers -> l'attention devrait briller.
3 acteurs, meme critique : AVEUGLE / RESUME (centroide) / ATTENTION.
"""
import sys, time, numpy as np, torch, torch.nn as nn
from torch.distributions import Categorical
DEV = "cuda:0" if torch.cuda.is_available() else "cpu"

class CoverHold:
    def __init__(self, N, A=6, G=12, T=30, iso_thr=4.0, iso_pen=0.4, R=2.5, seed=0):
        self.N, self.A, self.G, self.T, self.iso_thr, self.iso_pen, self.R = N, A, G, T, iso_thr, iso_pen, R
        self.n_actions = 5
        self.moves = torch.tensor([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]], device=DEV).float()
        self.cp = torch.tensor([[r, c] for r in (2, 6, 10) for c in (2, 6, 10)], device=DEV).float()  # 9 points repartis
        self.P = self.cp.shape[0]
        self.obs_dim = 2 + 2 * self.P
        self.g = torch.Generator(device=DEV); self.g.manual_seed(seed)
    def _rand(self, n): return torch.randint(0, self.G, (n, self.A, 2), generator=self.g, device=DEV).float()
    def reset(self):
        self.pos = self._rand(self.N); self.t = torch.zeros(self.N, device=DEV); return self._obs()
    def _obs(self):
        N, A, G = self.N, self.A, self.G
        own = self.pos / G
        cp_rel = (self.cp[None, None, :, :] - self.pos[:, :, None, :]) / G            # (N,A,P,2)
        own_feat = torch.cat([own, cp_rel.reshape(N, A, -1)], dim=2)                  # (N,A,2+2P)
        rel = (self.pos[:, None, :, :] - self.pos[:, :, None, :]) / G                 # (N,A,A,2)
        dist = rel.abs().sum(-1, keepdim=True)
        others = torch.cat([rel, dist], dim=3)                                        # (N,A,A,3)
        return own_feat, others
    def _metrics(self):
        dcp = (self.cp[:, None, :] - self.pos[:, :, :]).abs().sum(-1) if False else \
              (self.cp[None, :, None, :] - self.pos[:, None, :, :]).abs().sum(-1)     # (N,P,A)
        mind_cp = dcp.min(2).values                                                   # (N,P)
        cover = torch.exp(-mind_cp / self.R).mean(1)                                  # (N,) couverture douce [0,1]
        covered = (mind_cp <= self.R).float().mean(1)                                 # (N,) fraction points tenus
        dag = (self.pos[:, :, None, :] - self.pos[:, None, :, :]).abs().sum(-1)        # (N,A,A)
        dag = dag + torch.eye(self.A, device=DEV)[None] * 1e6                          # ignore soi
        nearest = dag.min(2).values                                                   # (N,A) dist au + proche coequipier
        iso = torch.relu(nearest - self.iso_thr).mean(1) / self.G                      # (N,)
        return cover, covered, iso, nearest.mean(1) / self.G
    def step(self, acts):
        self.pos = (self.pos + self.moves[acts]).clamp(0, self.G - 1)
        cover, covered, iso, spread = self._metrics()
        rew = cover - self.iso_pen * iso
        self.t += 1; done = self.t >= self.T
        info = {"covered": covered, "iso": iso, "spread": spread}
        if done.any():
            m = done; self.pos[m] = self._rand(int(m.sum())); self.t[m] = 0
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
        cen = (ot * mask).sum(2) / (A - 1)
        return self.net(torch.cat([of, cen], dim=2))

class AttnActor(nn.Module):
    def __init__(self, od, na, H=64, heads=4):
        super().__init__()
        self.own = nn.Sequential(nn.Linear(od, H), nn.Tanh()); self.kv = nn.Linear(3, H)
        self.attn = nn.MultiheadAttention(H, heads, batch_first=True)
        self.head = nn.Sequential(nn.Linear(2 * H, H), nn.Tanh(), nn.Linear(H, na))
    def logits(self, of, ot):
        N, A, _, _ = ot.shape
        q = self.own(of); kv = torch.tanh(self.kv(ot))
        ctx, _ = self.attn(q.reshape(N * A, 1, -1), kv.reshape(N * A, A, -1), kv.reshape(N * A, A, -1))
        return self.head(torch.cat([q, ctx.reshape(N, A, -1)], dim=2))

class Critic(nn.Module):
    def __init__(self, od, H=64):
        super().__init__(); self.net = nn.Sequential(nn.Linear(od, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, 1))
    def value(self, of): return self.net(of).squeeze(-1).mean(-1)

def train(actor_cls, seed=0, iters=300, N=1024, A=6, T=30, lr=3e-4, clip=0.2, epochs=4, mbs=4, gamma=0.99, lam=0.95):
    env = CoverHold(N, A, T=T, seed=seed); of, ot = env.reset(); od = env.obs_dim
    torch.manual_seed(seed)
    actor = actor_cls(od, env.n_actions).to(DEV); critic = Critic(od).to(DEV)
    opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=lr)
    for it in range(iters):
        b_of = torch.zeros(T, N, A, od, device=DEV); b_ot = torch.zeros(T, N, A, A, 3, device=DEV)
        b_a = torch.zeros(T, N, A, dtype=torch.long, device=DEV); b_lp = torch.zeros(T, N, A, device=DEV)
        b_v = torch.zeros(T, N, device=DEV); b_r = torch.zeros(T, N, device=DEV); b_d = torch.zeros(T, N, device=DEV)
        for t in range(T):
            with torch.no_grad():
                dist = Categorical(logits=actor.logits(of, ot)); a = dist.sample(); v = critic.value(of)
            (of2, ot2), r, done, info = env.step(a)
            b_of[t] = of; b_ot[t] = ot; b_a[t] = a; b_lp[t] = dist.log_prob(a); b_v[t] = v; b_r[t] = r; b_d[t] = done.float()
            of, ot = of2, ot2
        with torch.no_grad(): last_v = critic.value(of)
        adv = torch.zeros(T, N, device=DEV); g = torch.zeros(N, device=DEV)
        for t in reversed(range(T)):
            nnt = 1 - b_d[t]; nv = last_v if t == T - 1 else b_v[t + 1]
            delta = b_r[t] + gamma * nv * nnt - b_v[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + b_v).reshape(T * N)
        fof = b_of.reshape(T * N, A, od); fot = b_ot.reshape(T * N, A, A, 3)
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
    # eval
    cov, iso = [], []; of, ot = env.reset()
    for _ in range(T * 4):
        with torch.no_grad(): a = Categorical(logits=actor.logits(of, ot)).sample()
        (of, ot), r, done, info = env.step(a); cov.append(info["covered"].mean().item()); iso.append(info["iso"].mean().item())
    return float(np.mean(cov[-T:])), float(np.mean(iso[-T:]))

if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 8 if SMOKE else 300; SEEDS = [0] if SMOKE else [0, 1, 2]
    print("=== MISSION #1 CoverHold (occuper-tenir) SMOKE=%s ===" % SMOKE, flush=True)
    res = {}
    for cls in [BlindActor, SummaryActor, AttnActor]:
        cv, iso = [], []
        for s in SEEDS:
            c, i = train(cls, seed=s, iters=ITERS); cv.append(c); iso.append(i)
            print("[%s] seed %d -> couverture %.3f isolement %.3f" % (cls.__name__, s, c, i), flush=True)
        res[cls.__name__] = (np.mean(cv), np.std(cv), np.mean(iso), np.std(iso))
    print("\n===== RESULTAT : couverture (haut=mieux) / isolement (bas=mieux) =====", flush=True)
    print("%-14s | couverture       | isolement" % "acteur", flush=True)
    for k, (cm, cs, im, isd) in res.items():
        print("%-14s | %.3f +/- %.3f   | %.3f +/- %.3f" % (k, cm, cs, im, isd), flush=True)
    print("COVERHOLD_DONE", flush=True)
