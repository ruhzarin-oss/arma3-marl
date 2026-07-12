"""MISSION « OSER PERCER » + axe AUDACE (idee de Younes : il faut attention ET audace).
Carte : agents en bas, OBJECTIF en haut, une BANDE DE FEU au milieu (y prendre des degats).
  - Percer = amener >=secure agents vivants dans l'objectif.
  - Traverser GROUPES = feu concentre (plus de degats) ; traverser ETALES = feu dilue (attention aide).
DEUX regimes de recompense :
  - PRUDENT : +objectif  -pertes.            -> optimum = rester a l'abri = NE PERCE PAS (timide).
  - AUDACE  : idem + PRESSION TEMPORELLE (penalite tant que pas perce) + progression vers l'objectif.
                                              -> il FAUT pousser.
Test 2x2 : acteur {resume, attention} x regime {prudent, audace}. Hypothese :
  seul ATTENTION + AUDACE perce BIEN (perce ET peu de pertes). Audace seule = perce mais cher ; sans audace = stalle.
"""
import sys, time, numpy as np, torch, torch.nn as nn
from torch.distributions import Categorical
DEV = "cuda:0" if torch.cuda.is_available() else "cpu"

class Breach:
    def __init__(self, N, A=6, G=12, T=40, audace=True, seed=0,
                 dmg=0.16, dens=0.6, cas_pen=0.8, breach_bonus=4.0, time_pen=0.04, secure=3):
        self.N, self.A, self.G, self.T, self.audace = N, A, G, T, audace
        self.dmg, self.dens, self.cas_pen, self.bb, self.tp, self.secure = dmg, dens, cas_pen, breach_bonus, time_pen, secure
        self.n_actions = 5
        self.moves = torch.tensor([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]], device=DEV).float()
        self.band = (G // 2 - 1, G // 2 + 1); self.obj_row = G - 2
        self.obj_c = torch.tensor([G - 1.0, (G - 1) / 2.0], device=DEV)
        self.g = torch.Generator(device=DEV); self.g.manual_seed(seed)
        self.start_lo, self.start_hi = 0, 1   # rangee de spawn (curriculum inverse)
        self.obs_dim = 6
    def reset(self):
        self.pos = torch.stack([torch.randint(self.start_lo, self.start_hi + 1, (self.N, self.A), generator=self.g, device=DEV).float(),
                                torch.randint(0, self.G, (self.N, self.A), generator=self.g, device=DEV).float()], -1)
        self.hp = torch.ones(self.N, self.A, device=DEV); self.alive = torch.ones(self.N, self.A, dtype=torch.bool, device=DEV)
        self.t = torch.zeros(self.N, device=DEV); self.secured = torch.zeros(self.N, dtype=torch.bool, device=DEV)
        self.prevd = self._sqd(); return self._obs()
    def _sqd(self):
        d = (self.obj_row - self.pos[:, :, 0]).clamp(min=0)
        a = self.alive.float(); return (d * a).sum(1) / a.sum(1).clamp(min=1)
    def _obs(self):
        N, A, G = self.N, self.A, self.G
        own = self.pos / (G - 1)
        dobj = (self.obj_c[None, None, :] - self.pos) / G
        inband = ((self.pos[:, :, 0] >= self.band[0]) & (self.pos[:, :, 0] <= self.band[1])).float()[..., None]
        own_feat = torch.cat([own, self.hp[..., None], dobj, inband], 2)        # (N,A,6)
        rel = (self.pos[:, None, :, :] - self.pos[:, :, None, :]) / G
        dist = rel.abs().sum(-1, keepdim=True)
        others = torch.cat([rel, dist], 3)                                       # (N,A,A,3)
        return own_feat, others
    def step(self, acts):
        mv = self.moves[acts] * self.alive[..., None]
        self.pos = (self.pos + mv).clamp(0, self.G - 1)
        inband = (self.pos[:, :, 0] >= self.band[0]) & (self.pos[:, :, 0] <= self.band[1]) & self.alive
        # densite locale dans la bande : nb d'allies vivants proches (<=2 cases)
        d = (self.pos[:, :, None, :] - self.pos[:, None, :, :]).abs().sum(-1)     # (N,A,A)
        close = ((d <= 2.0) & self.alive[:, None, :]).float().sum(2) - 1.0        # exclut soi
        crowd = close.clamp(min=0)
        dmg = self.dmg * (1 + self.dens * crowd) * inband.float()
        self.hp = self.hp - dmg
        newly_dead = (self.hp <= 0) & self.alive
        self.alive = self.alive & (self.hp > 0)
        in_obj = (self.pos[:, :, 0] >= self.obj_row) & self.alive
        sec_now = in_obj.sum(1) >= self.secure
        newly_sec = sec_now & (~self.secured); self.secured = self.secured | sec_now
        sqd = self._sqd(); prog = (self.prevd - sqd); self.prevd = sqd
        rew = self.bb * newly_sec.float() - self.cas_pen * newly_dead.float().sum(1)
        if self.audace:
            rew = rew + 0.5 * prog - self.tp * (~self.secured).float()
        self.t += 1
        done = self.secured | (self.t >= self.T) | (~self.alive.any(1))
        info = {"breached": self.secured.float(), "cas": (~self.alive).float().sum(1)}
        if done.any():
            m = done
            self.pos[m] = torch.stack([torch.randint(self.start_lo, self.start_hi + 1, (int(m.sum()), self.A), generator=self.g, device=DEV).float(),
                                       torch.randint(0, self.G, (int(m.sum()), self.A), generator=self.g, device=DEV).float()], -1)
            self.hp[m] = 1; self.alive[m] = True; self.t[m] = 0; self.secured[m] = False; self.prevd = self._sqd()
        return self._obs(), rew, done, info

class SummaryActor(nn.Module):
    def __init__(self, od, na, H=64):
        super().__init__(); self.net = nn.Sequential(nn.Linear(od + 3, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, na))
    def logits(self, of, ot):
        N, A, _, _ = ot.shape
        mask = (1 - torch.eye(A, device=ot.device)).view(1, A, A, 1)
        cen = (ot * mask).sum(2) / (A - 1)
        return self.net(torch.cat([of, cen], 2))

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
        return self.head(torch.cat([q, ctx.reshape(N, A, -1)], 2))

class Critic(nn.Module):
    def __init__(self, od, H=64):
        super().__init__(); self.net = nn.Sequential(nn.Linear(od, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, 1))
    def value(self, of): return self.net(of).squeeze(-1).mean(-1)

def train(actor_cls, audace, seed=0, iters=300, N=1024, A=6, T=40, lr=3e-4, clip=0.2, epochs=4, mbs=4, gamma=0.99, lam=0.95):
    env = Breach(N, A, T=T, audace=audace, seed=seed); of, ot = env.reset(); od = env.obs_dim
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
    br, cs = [], []; of, ot = env.reset()
    for _ in range(T * 5):
        with torch.no_grad(): a = Categorical(logits=actor.logits(of, ot)).sample()
        (of, ot), r, done, info = env.step(a)
        dm = done.bool()
        if dm.any(): br.append(info["breached"][dm].mean().item()); cs.append(info["cas"][dm].mean().item())
    return float(np.mean(br)) if br else 0.0, float(np.mean(cs)) if cs else 0.0

if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 8 if SMOKE else 300; SEEDS = [0] if SMOKE else [0, 1, 2]
    print("=== MISSION 'OSER PERCER' — attention x audace SMOKE=%s ===" % SMOKE, flush=True)
    cells = [("resume", SummaryActor, "prudent", False), ("resume", SummaryActor, "audace", True),
             ("attention", AttnActor, "prudent", False), ("attention", AttnActor, "audace", True)]
    res = {}
    for name, cls, reg, aud in cells:
        b, c = [], []
        for s in SEEDS:
            br, cs = train(cls, aud, seed=s, iters=ITERS); b.append(br); c.append(cs)
        res[(name, reg)] = (np.mean(b), np.std(b), np.mean(c), np.std(c))
        print("[%s + %s] perce=%.2f+/-%.2f  pertes=%.2f" % (name, reg, np.mean(b), np.std(b), np.mean(c)), flush=True)
    print("\n===== 2x2 : taux de PERCEE (haut=mieux) / pertes (bas=mieux) =====", flush=True)
    print("%-12s | %-18s | %-18s" % ("acteur", "PRUDENT", "AUDACE"), flush=True)
    for name in ["resume", "attention"]:
        p = res[(name, "prudent")]; a = res[(name, "audace")]
        print("%-12s | perce %.2f pertes %.2f | perce %.2f pertes %.2f" % (name, p[0], p[2], a[0], a[2]), flush=True)
    print("BREACH_DONE", flush=True)
