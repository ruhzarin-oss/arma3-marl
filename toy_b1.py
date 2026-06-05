"""toy_b1 — simulateur NumPy RAPIDE calé EXACTEMENT sur l'observation de l'env Arma B1.
Meme obs/agent (10) et memes 5 actions -> une politique entrainee ici TRANSFERE directement dans Arma B1.
Combat abstrait par proximite + accumulation de degats (comme le plafond 0.85 d'Arma) : les deux camps se neutralisent.
Des milliers de mondes en parallele -> millions de pas en quelques minutes (pre-entrainement)."""
import numpy as np


class ToyB1:
    def __init__(self, num_envs=4096, n=4, opfor=3, obj_dist=160.0, move=22.0,
                 secure_r=28.0, secure_n=3, threat_range=110.0, max_steps=22,
                 dmg_dead=0.7, hit=0.16, kill=0.14, beta=0.7, seed=0):
        self.N = num_envs; self.A = n; self.K = opfor
        self.obj_dist = obj_dist; self.move = move; self.secure_r = secure_r
        self.secure_n = secure_n; self.threat_range = threat_range; self.max_steps = max_steps
        self.dmg_dead = dmg_dead; self.hit = hit; self.kill = kill; self.beta = beta
        self.scale = float(obj_dist); self.n_actions = 5; self.obs_dim = 10
        self.rng = np.random.default_rng(seed)
        self.DELTA = np.array([[0, 0], [0, 1], [0, -1], [1, 0], [-1, 0]], dtype=np.float32)
        self._alloc()

    def _alloc(self):
        N, A, K = self.N, self.A, self.K
        self.basex = np.zeros(N); self.basey = np.zeros(N)
        self.objx = np.zeros(N); self.objy = np.zeros(N)
        self.px = np.zeros((N, A)); self.py = np.zeros((N, A)); self.admg = np.zeros((N, A))
        self.ox = np.zeros((N, K)); self.oy = np.zeros((N, K)); self.odmg = np.zeros((N, K))
        self.t = np.zeros(N, dtype=int); self.secured = np.zeros(N, dtype=bool)
        self.prev_alive = np.full(N, A); self.prev_d = np.zeros(N)

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        A, K = self.A, self.K
        # base + objectif (objectif a l'Est, distance fixe ; petite variation aleatoire)
        bx = self.rng.uniform(-40, 40, n); by = self.rng.uniform(-40, 40, n)
        self.basex[idx] = bx; self.basey[idx] = by
        ang = self.rng.uniform(-0.5, 0.5, n)
        self.objx[idx] = bx + self.obj_dist * np.cos(ang); self.objy[idx] = by + self.obj_dist * np.sin(ang)
        # agents groupes autour de la base
        ax = bx[:, None] + (np.arange(A)[None, :] % 2) * 6 - 3
        ay = by[:, None] + (np.arange(A)[None, :] // 2) * 6 - 3
        self.px[idx] = ax; self.py[idx] = ay; self.admg[idx] = 0.0
        # defenseurs autour de l'objectif
        ox = self.objx[idx][:, None] + (np.arange(K)[None, :] - 1) * 10
        oy = self.objy[idx][:, None] + (np.arange(K)[None, :] - 1) * 12
        self.ox[idx] = ox; self.oy[idx] = oy; self.odmg[idx] = 0.0
        self.t[idx] = self.rng.integers(0, self.max_steps, n)
        self.secured[idx] = False; self.prev_alive[idx] = A
        self.prev_d[idx] = self._mean_dist(idx)

    def _alive(self):
        return self.admg < self.dmg_dead

    def _oalive(self):
        return self.odmg < self.dmg_dead

    def _mean_dist(self, idx=None):
        if idx is None:
            px, py, objx, objy, al = self.px, self.py, self.objx, self.objy, self._alive()
        else:
            px, py, objx, objy = self.px[idx], self.py[idx], self.objx[idx], self.objy[idx]
            al = (self.admg[idx] < self.dmg_dead)
        d = np.sqrt((px - objx[:, None]) ** 2 + (py - objy[:, None]) ** 2) / self.scale
        den = al.sum(1)
        return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self._reset_rows(np.arange(self.N))
        return self._obs()

    def _obs(self):
        S = self.scale
        al = self._alive(); oal = self._oalive()
        ox = (self.px - self.basex[:, None]) / S; oy = (self.py - self.basey[:, None]) / S
        dgx = (self.objx[:, None] - self.px) / S; dgy = (self.objy[:, None] - self.py) / S
        # plus proche coequipier vivant
        dx = self.px[:, None, :] - self.px[:, :, None]; dy = self.py[:, None, :] - self.py[:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, self.A, self.A)),
                      1e18, dx * dx + dy * dy)
        jmin = d2.argmin(2)
        mdx = np.take_along_axis(dx, jmin[:, :, None], 2)[:, :, 0] / S
        mdy = np.take_along_axis(dy, jmin[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; mdx[nm] = 0.0; mdy[nm] = 0.0
        # plus proche defenseur vivant
        tx = self.ox[:, None, :] - self.px[:, :, None]; ty = self.oy[:, None, :] - self.py[:, :, None]
        td2 = np.where(oal[:, None, :], tx * tx + ty * ty, 1e18)
        kmin = td2.argmin(2)
        nox = np.take_along_axis(tx, kmin[:, :, None], 2)[:, :, 0] / S
        noy = np.take_along_axis(ty, kmin[:, :, None], 2)[:, :, 0] / S
        nd = td2.min(2) >= 1e18; nox[nd] = 0.0; noy[nd] = 0.0
        ndist = np.sqrt(np.where(nd, (self.threat_range * 3) ** 2, td2.min(2)))
        tprox = np.clip(1.0 - ndist / self.threat_range, 0.0, 1.0)
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), mdx, mdy, nox, noy, tprox], axis=2).astype(np.float32)

    def step(self, actions, auto_reset=True):
        a = np.asarray(actions).astype(int)
        al = self._alive()
        d = self.DELTA[a]  # (N,A,2)
        self.px = self.px + d[:, :, 0] * self.move * al
        self.py = self.py + d[:, :, 1] * self.move * al
        # --- combat abstrait : degats par proximite ---
        oal = self._oalive()
        # agents touches par le plus proche defenseur vivant
        tx = self.ox[:, None, :] - self.px[:, :, None]; ty = self.oy[:, None, :] - self.py[:, :, None]
        td2 = np.where(oal[:, None, :], tx * tx + ty * ty, 1e18)
        admin = np.sqrt(td2.min(2))  # (N,A) dist au defenseur le + proche
        a_expose = np.clip(1.0 - admin / self.threat_range, 0.0, 1.0)
        self.admg = np.minimum(0.85, self.admg + self.hit * a_expose * al)
        # defenseurs neutralises par le plus proche agent vivant
        al2 = self._alive()
        ux = self.px[:, None, :] - self.ox[:, :, None]; uy = self.py[:, None, :] - self.oy[:, :, None]
        ud2 = np.where(al2[:, None, :], ux * ux + uy * uy, 1e18)
        odmin = np.sqrt(ud2.min(2))  # (N,K) dist a l'agent le + proche
        o_expose = np.clip(1.0 - odmin / self.threat_range, 0.0, 1.0)
        self.odmg = np.minimum(0.85, self.odmg + self.kill * o_expose * oal)
        # --- recompense ---
        al = self._alive(); n_alive = al.sum(1)
        d2obj = (self.px - self.objx[:, None]) ** 2 + (self.py - self.objy[:, None]) ** 2
        in_obj = ((d2obj <= self.secure_r ** 2) & al).sum(1)
        secured = in_obj >= self.secure_n
        newly = secured & (~self.secured)
        cost = np.maximum(0, self.prev_alive - n_alive).astype(np.float32)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps) | (n_alive == 0)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = newly.astype(np.float32) - 0.01 + shaping.astype(np.float32)
        self.secured = secured.copy(); self.prev_alive = n_alive.astype(int)
        done_out = done.copy()
        info = {"success": secured.copy(), "alive": n_alive.copy(),
                "opf_alive": self._oalive().sum(1).copy()}
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return self._obs(), rew, cost, done_out.astype(np.float32), info


if __name__ == "__main__":
    import time
    env = ToyB1(num_envs=4096)
    obs = env.reset(); print("obs", obs.shape)
    t0 = time.time(); steps = 200
    for _ in range(steps):
        a = np.random.randint(0, 5, (env.N, env.A))
        env.step(a)
    print("debit toy_b1: %.0f transitions/s" % (env.N * steps / (time.time() - t0)))
