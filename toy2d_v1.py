"""Harmattan v1 — simulateur à RÔLES (capacités fixes + scénario qui force la coopération).

Roles (index fixe) : 0=Chef (standard), 1=Mitrailleur, 2=Médecin, 3=Éclaireur.
Capacités (action de rôle = action 5) :
  - Mitrailleur : suppresse les cases de danger autour de lui (rayon 1) pour `suppress_dur` pas.
  - Médecin : relève les coéquipiers À TERRE adjacents (rayon 1).
  - Éclaireur : vision élargie (passif).
États d'un agent : ALIVE(2)=agit, DOWN(1)=à terre (réanimable, sinon meurt après `bleed` pas), DEAD(0).
Scénario : une BANDE DE DANGER (ligne 6, toutes colonnes) barre le chemin vers l'objectif.
Coût (CMDP) = morts définitives. Réussite = >=3 agents VIVANTS dans la zone-objectif.
"""
import numpy as np
ALIVE, DOWN, DEAD = 2, 1, 0
CHEF, MG, MEDIC, SCOUT = 0, 1, 2, 3


class VectorizedToy2Dv1:
    def __init__(self, num_envs=512, grid=12, max_steps=120, p_hit=0.25,
                 secure_count=3, gamma=0.99, bleed=6, suppress_dur=5, seed=0):
        self.N, self.G, self.A = num_envs, grid, 4
        self.max_steps, self.p_hit, self.secure_count = max_steps, p_hit, secure_count
        self.gamma, self.bleed, self.suppress_dur = gamma, bleed, suppress_dur
        self.rng = np.random.default_rng(seed)
        self.roles = np.array([CHEF, MG, MEDIC, SCOUT])
        self.vision = np.array([4, 4, 4, 7])
        self.obj_lo = np.array([grid - 2, grid - 2]); self.obj_hi = np.array([grid - 1, grid - 1])
        self.obj_center = (self.obj_lo + self.obj_hi) / 2.0
        self.danger = np.array([[6, c] for c in range(grid)]); self.D = len(self.danger)
        self.moves = np.array([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]])
        self.n_actions = 6
        self.obs_dim = 2 + 2 + 2 + 4 + 2 + 1 + 2 + 1 + 2 + 1  # = 19
        self._alloc()

    def _alloc(self):
        self.pos = np.zeros((self.N, self.A, 2), dtype=np.int32)
        self.state = np.full((self.N, self.A), ALIVE, dtype=np.int8)
        self.bleed_t = np.zeros((self.N, self.A), dtype=np.int32)
        self.suppress_t = np.zeros((self.N, self.D), dtype=np.int32)
        self.t = np.zeros(self.N, dtype=np.int32)
        self.done = np.zeros(self.N, dtype=bool); self.success = np.zeros(self.N, dtype=bool)
        self.prev_phi = np.zeros(self.N, dtype=np.float32)
        self.reset()

    def reset(self, mask=None):
        if mask is None: mask = np.ones(self.N, dtype=bool)
        idx = np.where(mask)[0]
        starts = np.array([[1, 5], [1, 6], [2, 5], [2, 6]])
        self.pos[idx] = starts[None]; self.state[idx] = ALIVE; self.bleed_t[idx] = 0
        self.suppress_t[idx] = 0; self.t[idx] = 0; self.done[idx] = False; self.success[idx] = False
        self.prev_phi[idx] = self._phi()[idx]
        return self._get_obs()

    def _alive(self): return self.state == ALIVE

    def _phi(self):
        d = np.abs(self.pos - self.obj_center[None, None, :]).sum(-1)
        al = self._alive().astype(np.float32)
        return (-((d * al).sum(1) / np.maximum(al.sum(1), 1.0)) / (2 * self.G)).astype(np.float32)

    def _in_obj(self):
        ge = (self.pos >= self.obj_lo[None, None, :]).all(-1)
        le = (self.pos <= self.obj_hi[None, None, :]).all(-1)
        return ge & le & self._alive()

    def step(self, actions, auto_reset=True):
        al = self._alive()
        mv = np.where(actions == 5, 0, actions)
        self.pos = np.clip(self.pos + self.moves[mv] * al[..., None], 0, self.G - 1)
        self.suppress_t = np.maximum(self.suppress_t - 1, 0)
        # Mitrailleur : suppression (rayon 1) si vivant et action de rôle
        cond_mg = (self.state[:, MG] == ALIVE) & (actions[:, MG] == 5)
        cheb = np.abs(self.danger[None, :, :] - self.pos[:, MG, None, :]).max(-1)
        self.suppress_t = np.where(cond_mg[:, None] & (cheb <= 1), self.suppress_dur, self.suppress_t)
        # Médecin : réanimation des adjacents à terre
        cond_med = (self.state[:, MEDIC] == ALIVE) & (actions[:, MEDIC] == 5)
        for j in range(self.A):
            if j == MEDIC: continue
            ch = np.abs(self.pos[:, j, :] - self.pos[:, MEDIC, :]).max(-1)
            rev = cond_med & (self.state[:, j] == DOWN) & (ch <= 1)
            self.state[rev, j] = ALIVE; self.bleed_t[rev, j] = 0
        # progression des agents à terre -> mort
        downmask = self.state == DOWN
        self.bleed_t[downmask] -= 1
        new_dead = (self.state == DOWN) & (self.bleed_t <= 0)
        self.state[new_dead] = DEAD
        casualties = new_dead.sum(1).astype(np.float32)
        # danger actif -> nouveaux agents à terre
        on_row = self.pos[..., 0] == self.danger[0, 0]
        col = np.clip(self.pos[..., 1], 0, self.D - 1)
        supp_here = np.take_along_axis(self.suppress_t, col, axis=1)
        active_here = on_row & (supp_here <= 0) & self._alive()
        hit = active_here & (self.rng.random((self.N, self.A)) < self.p_hit)
        self.state[hit] = DOWN; self.bleed_t[hit] = self.bleed
        # fin / récompense
        secured = self._in_obj().sum(1) >= self.secure_count
        newly = secured & ~self.success; self.success |= secured
        self.t += 1
        wiped = ~self._alive().any(1)
        self.done = self.success | (self.t >= self.max_steps) | wiped
        phi = self._phi(); shaping = self.gamma * phi - self.prev_phi; self.prev_phi = phi
        reward = newly.astype(np.float32) + shaping - 0.01
        info = {"success": self.success.copy(), "casualties": casualties}
        done_out = self.done.copy()
        if auto_reset and self.done.any(): self.reset(self.done)
        return self._get_obs(), reward, casualties, done_out, info

    def _get_obs(self):
        N, A, G = self.N, self.A, self.G
        pos = self.pos.astype(np.float32); own = pos / (G - 1)
        dir_obj = (self.obj_center[None, None, :] - pos) / G
        alive = self._alive(); down = self.state == DOWN
        role_oh = np.eye(4, dtype=np.float32)[self.roles]
        dgr = self.danger.astype(np.float32); active = self.suppress_t <= 0
        obs = np.zeros((N, A, self.obs_dim), dtype=np.float32)
        for i in range(A):
            p = pos[:, i, :]; vis = int(self.vision[self.roles[i]])
            st = np.stack([alive[:, i].astype(np.float32), down[:, i].astype(np.float32)], 1)
            others = [j for j in range(A) if j != i]
            rel = pos[:, others, :] - p[:, None, :]; dist = np.abs(rel).sum(-1)
            vm = (alive[:, others] & (dist <= vis)).astype(np.float32); cnt = vm.sum(1)
            cen = (rel * vm[..., None]).sum(1) / np.maximum(cnt[:, None], 1.0) / G
            reld = dgr[None] - p[:, None, :]; dd = np.abs(reld).sum(-1); k = dd.argmin(1)
            nd_rel = reld[np.arange(N), k, :] / G
            nd_vis = (dd[np.arange(N), k] <= vis).astype(np.float32)
            nd_flag = (active[np.arange(N), k].astype(np.float32) * nd_vis)[:, None]
            nd_rel = nd_rel * nd_vis[:, None]
            dmask = down[:, others] & (dist <= vis)
            big = np.where(dmask, dist, 1e9); kk = big.argmin(1)
            has_down = dmask.any(1).astype(np.float32)
            dn_rel = rel[np.arange(N), kk, :] / G * has_down[:, None]
            obs[:, i, :] = np.concatenate([own[:, i, :], dir_obj[:, i, :], st,
                np.broadcast_to(role_oh[i], (N, 4)), cen, (cnt / A)[:, None],
                nd_rel, nd_flag, dn_rel, has_down[:, None]], axis=1)
        return obs


if __name__ == "__main__":
    import time
    env = VectorizedToy2Dv1(num_envs=1024, seed=0); obs = env.reset()
    print(f"v1 | obs/agent={env.obs_dim} | actions={env.n_actions} | obs={obs.shape}")
    rng = np.random.default_rng(1); steps = 1000; t0 = time.time(); deaths = 0.0
    for _ in range(steps):
        a = rng.integers(0, env.n_actions, size=(env.N, env.A))
        obs, r, c, d, info = env.step(a); deaths += float(c.sum())
    dt = time.time() - t0; tot = steps * env.N
    print(f"{tot:,} transitions en {dt:.2f}s -> {tot/dt:,.0f}/s | morts def. (aleatoire): {deaths:,.0f}")
    print("mecaniques OK (pas de crash)")
