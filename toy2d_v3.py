"""Harmattan v3 — ARBITRAGE du chef (sergent). DEUX objectifs (gauche/droite).
On gagne si >=3 agents VIVANTS sécurisent LE MÊME objectif. À chaque épisode, un côté est
'bloqué' (danger létal sur son approche) tiré au hasard : le chef doit orienter l'équipe vers
le côté OUVERT et faire converger tout le monde. Curriculum : level 0 = sans danger (apprendre
à converger), level 1 = avec danger (apprendre à arbitrer). Le chef avance et risque comme les autres.
"""
import numpy as np
CHEF, MG, MEDIC, SCOUT = 0, 1, 2, 3

class VectorizedToy2Dv3:
    def __init__(self, num_envs=512, grid=12, max_steps=80, p_hit=0.3, secure_count=3, gamma=0.99, level=1, seed=0):
        self.N, self.G, self.A = num_envs, grid, 4
        self.max_steps, self.p_hit, self.secure_count, self.gamma, self.level = max_steps, p_hit, secure_count, gamma, level
        self.rng = np.random.default_rng(seed)
        self.roles = np.array([CHEF, MG, MEDIC, SCOUT]); self.vision = np.array([4, 4, 4, 7])
        self.objL_lo = np.array([grid-2, 1]); self.objL_hi = np.array([grid-1, 2])
        self.objR_lo = np.array([grid-2, grid-3]); self.objR_hi = np.array([grid-1, grid-2])
        self.objL_c = (self.objL_lo+self.objL_hi)/2.0; self.objR_c = (self.objR_lo+self.objR_hi)/2.0
        self.moves = np.array([[0,0],[-1,0],[1,0],[0,-1],[0,1]]); self.n_actions = 5; self.n_obj = 2
        self.sense_range = 4
        self.dcells = np.array([[r, c] for r in (8, 9) for c in list(range(0, 5)) + list(range(7, grid))])
        self.cell_left = self.dcells[:, 1] <= 4; self.cell_right = self.dcells[:, 1] >= 7
        self.obs_dim = 14
        self._alloc()
    def _alloc(self):
        self.pos = np.zeros((self.N, self.A, 2), dtype=np.int32); self.alive = np.ones((self.N, self.A), dtype=bool)
        self.blocked = np.zeros(self.N, dtype=np.int8)
        self.t = np.zeros(self.N, dtype=np.int32); self.done = np.zeros(self.N, dtype=bool); self.success = np.zeros(self.N, dtype=bool)
        self.prev_phi = np.zeros(self.N, dtype=np.float32); self.reset()
    def set_level(self, lv): self.level = lv
    def reset(self, mask=None):
        if mask is None: mask = np.ones(self.N, dtype=bool)
        idx = np.where(mask)[0]
        self.pos[idx] = np.array([[1,5],[1,6],[2,5],[2,6]])[None]; self.alive[idx] = True
        self.blocked[idx] = self.rng.integers(0, 2, size=len(idx)).astype(np.int8)
        self.t[idx] = 0; self.done[idx] = False; self.success[idx] = False; self.prev_phi[idx] = self._phi()[idx]
        return self._get_obs()
    def _danger_active(self):
        if self.level < 1: return np.zeros((self.N, self.A), dtype=bool)
        row = self.pos[..., 0]; col = self.pos[..., 1]; inrow = (row == 8) | (row == 9); bl = self.blocked[:, None]
        return inrow & (((bl == 0) & (col <= 4)) | ((bl == 1) & (col >= 7)))
    def _phi(self):
        openc = np.where((self.blocked == 0)[:, None, None], self.objR_c[None, None, :], self.objL_c[None, None, :])
        d = np.abs(self.pos - openc).sum(-1); al = self.alive.astype(np.float32)
        return (-((d * al).sum(1) / np.maximum(al.sum(1), 1.0)) / (2 * self.G)).astype(np.float32)
    def _count_in(self, lo, hi):
        return ((self.pos >= lo[None, None, :]).all(-1) & (self.pos <= hi[None, None, :]).all(-1) & self.alive).sum(1)
    def step(self, actions, auto_reset=True):
        self.pos = np.clip(self.pos + self.moves[actions] * self.alive[..., None], 0, self.G - 1)
        hit = self._danger_active() & self.alive & (self.rng.random((self.N, self.A)) < self.p_hit)
        self.alive &= ~hit; casualties = hit.sum(1).astype(np.float32)
        secured = (self._count_in(self.objL_lo, self.objL_hi) >= self.secure_count) | (self._count_in(self.objR_lo, self.objR_hi) >= self.secure_count)
        newly = secured & ~self.success; self.success |= secured
        self.t += 1; wiped = ~self.alive.any(1); self.done = self.success | (self.t >= self.max_steps) | wiped
        phi = self._phi(); shaping = self.gamma * phi - self.prev_phi; self.prev_phi = phi
        reward = newly.astype(np.float32) + shaping - 0.01
        info = {"success": self.success.copy(), "casualties": casualties}; done_out = self.done.copy()
        if auto_reset and self.done.any(): self.reset(self.done)
        return self._get_obs(), reward, casualties, done_out, info
    def _get_obs(self):
        N, A, G = self.N, self.A, self.G; pos = self.pos.astype(np.float32); own = pos / (G - 1)
        indang = self._danger_active().astype(np.float32); alive = self.alive; role_oh = np.eye(4, dtype=np.float32)[self.roles]
        if self.level >= 1:
            active = (self.cell_left[None, :] & (self.blocked[:, None] == 0)) | (self.cell_right[None, :] & (self.blocked[:, None] == 1))
        else:
            active = np.zeros((N, self.dcells.shape[0]), dtype=bool)
        dc = self.dcells.astype(np.float32)
        obs = np.zeros((N, A, self.obs_dim), dtype=np.float32)
        for i in range(A):
            p = pos[:, i, :]; vis = int(self.vision[self.roles[i]]); others = [j for j in range(A) if j != i]
            rel = pos[:, others, :] - p[:, None, :]; dist = np.abs(rel).sum(-1)
            vm = (alive[:, others] & (dist <= vis)).astype(np.float32); cnt = vm.sum(1)
            cen = (rel * vm[..., None]).sum(1) / np.maximum(cnt[:, None], 1.0) / G
            reld = dc[None] - p[:, None, :]; dd = np.abs(reld).sum(-1)
            big = np.where(active & (dd <= self.sense_range), dd, 1e9); k = big.argmin(1)
            seen = (big[np.arange(N), k] < 1e9).astype(np.float32); ld = reld[np.arange(N), k, :] / G * seen[:, None]
            obs[:, i, :] = np.concatenate([own[:, i, :], ld, seen[:, None], indang[:, i:i+1],
                np.broadcast_to(role_oh[i], (N, 4)), cen, (cnt / A)[:, None], alive[:, i:i+1].astype(np.float32)], axis=1)
        return obs

if __name__ == "__main__":
    import time
    for lv in [0, 1]:
        env = VectorizedToy2Dv3(num_envs=1024, level=lv, seed=0); env.reset()
        rng = np.random.default_rng(1); steps = 600; t0 = time.time(); deaths = 0.0
        for _ in range(steps):
            a = rng.integers(0, env.n_actions, size=(env.N, env.A)); o, r, c, d, info = env.step(a); deaths += float(c.sum())
        dt = time.time() - t0; tot = steps * env.N
        print(f"level {lv} | obs={o.shape} | {tot/dt:,.0f} trans/s | morts(alea)={deaths:,.0f}")
    print("v3 mecaniques OK")
