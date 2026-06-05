"""Harmattan v4 — DOCTRINE 'suivre le chef' (cohésion). 4 soldats, agent 0 = CHEF qui mène.
Les soldats sont conditionnés au chef : ils voient sa position relative + une récompense de
cohésion les pousse à rester en formation derrière lui. Bande de danger (ligne drow) avec une
OUVERTURE aléatoire : le chef trouve l'ouverture et la franchit ; les soldats en formation passent."""
import numpy as np
CHIEF = 0

class VectorizedToy2Dv4:
    def __init__(self, num_envs=512, grid=14, max_steps=100, p_hit=0.35, secure_count=3,
                 gamma=0.99, w_coh=0.02, drow=7, gap=3, seed=0):
        self.N, self.G, self.A = num_envs, grid, 4
        self.max_steps, self.p_hit, self.secure_count, self.gamma = max_steps, p_hit, secure_count, gamma
        self.w_coh, self.drow, self.gapw = w_coh, drow, gap
        self.rng = np.random.default_rng(seed); self.vision = np.array([5, 5, 5, 5])
        self.obj_lo = np.array([grid - 2, grid // 2 - 1]); self.obj_hi = np.array([grid - 1, grid // 2 + 1])
        self.obj_c = (self.obj_lo + self.obj_hi) / 2.0
        self.moves = np.array([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]]); self.n_actions = 5; self.sense = 4
        self.obs_dim = 13
        self._alloc()
    def _alloc(self):
        self.pos = np.zeros((self.N, self.A, 2), dtype=np.int32); self.alive = np.ones((self.N, self.A), dtype=bool)
        self.gap = np.zeros(self.N, dtype=np.int32); self.t = np.zeros(self.N, dtype=np.int32)
        self.done = np.zeros(self.N, dtype=bool); self.success = np.zeros(self.N, dtype=bool); self.prev_phi = np.zeros(self.N, dtype=np.float32)
        self.reset()
    def reset(self, mask=None):
        if mask is None: mask = np.ones(self.N, dtype=bool)
        idx = np.where(mask)[0]; c = self.G // 2
        self.pos[idx] = np.array([[1, c], [1, c - 1], [2, c], [2, c - 1]])[None]; self.alive[idx] = True
        self.gap[idx] = self.rng.integers(0, self.G - self.gapw, size=len(idx))
        self.t[idx] = 0; self.done[idx] = False; self.success[idx] = False; self.prev_phi[idx] = self._phi()[idx]
        return self._get_obs()
    def _is_danger(self, row, col):
        ingap = (col >= self.gap[:, None]) & (col < self.gap[:, None] + self.gapw)
        return (row == self.drow) & ~ingap
    def _phi(self):
        d = np.abs(self.pos - self.obj_c[None, None, :]).sum(-1); al = self.alive.astype(np.float32)
        return (-((d * al).sum(1) / np.maximum(al.sum(1), 1.0)) / (2 * self.G)).astype(np.float32)
    def _cohesion(self):
        cp = self.pos[:, CHIEF, :].astype(np.float32); sd = np.abs(self.pos[:, 1:, :].astype(np.float32) - cp[:, None, :]).sum(-1)
        als = self.alive[:, 1:].astype(np.float32)
        return (np.exp(-sd / 3.0) * als).sum(1) / np.maximum(als.sum(1), 1.0)
    def step(self, actions, auto_reset=True):
        self.pos = np.clip(self.pos + self.moves[actions] * self.alive[..., None], 0, self.G - 1)
        hit = self._is_danger(self.pos[..., 0], self.pos[..., 1]) & self.alive & (self.rng.random((self.N, self.A)) < self.p_hit)
        self.alive &= ~hit; casualties = hit.sum(1).astype(np.float32)
        ge = (self.pos >= self.obj_lo[None, None, :]).all(-1); le = (self.pos <= self.obj_hi[None, None, :]).all(-1)
        secured = (ge & le & self.alive).sum(1) >= self.secure_count; newly = secured & ~self.success; self.success |= secured
        self.t += 1; wiped = ~self.alive.any(1); self.done = self.success | (self.t >= self.max_steps) | wiped
        phi = self._phi(); shaping = self.gamma * phi - self.prev_phi; self.prev_phi = phi; coh = self._cohesion()
        reward = newly.astype(np.float32) + shaping + self.w_coh * coh - 0.01
        info = {"success": self.success.copy(), "casualties": casualties, "cohesion": coh}; done_out = self.done.copy()
        if auto_reset and self.done.any(): self.reset(self.done)
        return self._get_obs(), reward, casualties, done_out, info
    def _get_obs(self):
        N, A, G = self.N, self.A, self.G; pos = self.pos.astype(np.float32); own = pos / (G - 1)
        dirobj = (self.obj_c[None, None, :] - pos) / G; cp = pos[:, CHIEF, :]; alive = self.alive
        cols = np.arange(G); obs = np.zeros((N, A, self.obs_dim), dtype=np.float32)
        ingap = (cols[None, :] >= self.gap[:, None]) & (cols[None, :] < self.gap[:, None] + self.gapw)
        for i in range(A):
            p = pos[:, i, :]; others = [j for j in range(A) if j != i]
            rel = pos[:, others, :] - p[:, None, :]; dist = np.abs(rel).sum(-1)
            vm = (alive[:, others] & (dist <= int(self.vision[i]))).astype(np.float32); cnt = vm.sum(1)
            cen = (rel * vm[..., None]).sum(1) / np.maximum(cnt[:, None], 1.0) / G
            cell_d = np.abs(cols[None, :] - p[:, 1:2]) + np.abs(self.drow - p[:, 0:1])
            big = np.where((~ingap) & (cell_d <= self.sense), cell_d, 1e9); k = big.argmin(1)
            seen = (big[np.arange(N), k] < 1e9).astype(np.float32)
            ld = np.stack([(self.drow - p[:, 0]) / G, (cols[k] - p[:, 1]) / G], 1) * seen[:, None]
            chief_rel = (cp - p) / G; ischief = np.full((N, 1), 1.0 if i == CHIEF else 0.0, dtype=np.float32)
            obs[:, i, :] = np.concatenate([own[:, i, :], dirobj[:, i, :], ld, seen[:, None], chief_rel, ischief, cen, alive[:, i:i+1].astype(np.float32)], axis=1)
        return obs

if __name__ == "__main__":
    import time
    env = VectorizedToy2Dv4(num_envs=1024, seed=0); env.reset(); rng = np.random.default_rng(1)
    steps = 500; t0 = time.time(); deaths = 0.0; coh = 0.0
    for _ in range(steps):
        a = rng.integers(0, env.n_actions, size=(env.N, env.A)); o, r, c, d, info = env.step(a); deaths += float(c.sum()); coh += float(info["cohesion"].mean())
    dt = time.time() - t0; tot = steps * env.N
    print(f"obs={o.shape} | {tot/dt:,.0f} trans/s | morts(alea)={deaths:,.0f} | cohesion moy={coh/steps:.2f}")
    print("v4 OK")
