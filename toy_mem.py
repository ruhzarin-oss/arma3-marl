"""toy_mem — tache de MEMOIRE (observation partielle). L'objectif n'est VISIBLE qu'aux premiers pas,
puis CACHE. Pour l'atteindre, l'agent doit s'en SOUVENIR. Une politique sans memoire echoue
(apres le masquage, plus aucune info sur l'objectif, qui est aleatoire chaque episode) ;
une politique recurrente (GRU) se souvient -> reussit. NumPy vectorise, ultra-rapide.
obs/agent = 7 : [own_x, own_y, goal_x(masque), goal_y(masque), visible, mate_dx, mate_dy] (normalises)."""
import numpy as np


class ToyMem:
    def __init__(self, num_envs=512, n=4, size=12.0, move=1.0, reach_r=1.6, secure_n=3,
                 vis_steps=2, max_steps=24, beta=0.3, seed=0):
        self.N = num_envs; self.A = n; self.size = size; self.move = move
        self.reach_r = reach_r; self.secure_n = secure_n; self.vis_steps = vis_steps
        self.max_steps = max_steps; self.beta = beta
        self.obs_dim = 7; self.n_actions = 5; self.scale = size
        self.rng = np.random.default_rng(seed)
        self.DELTA = np.array([[0, 0], [0, 1], [0, -1], [1, 0], [-1, 0]], dtype=np.float32)
        self.px = np.zeros((self.N, self.A)); self.py = np.zeros((self.N, self.A))
        self.gx = np.zeros(self.N); self.gy = np.zeros(self.N)
        self.t = np.zeros(self.N, dtype=int); self.secured = np.zeros(self.N, dtype=bool)
        self.prev_d = np.zeros(self.N)

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        c = self.size / 2.0
        self.px[idx] = c + self.rng.uniform(-1.5, 1.5, (n, self.A))
        self.py[idx] = c + self.rng.uniform(-1.5, 1.5, (n, self.A))
        # objectif aleatoire, suffisamment loin (memoire necessaire)
        ang = self.rng.uniform(0, 2 * np.pi, n); rad = self.rng.uniform(0.55, 0.8, n) * (self.size / 2)
        self.gx[idx] = c + rad * np.cos(ang); self.gy[idx] = c + rad * np.sin(ang)
        self.t[idx] = 0; self.secured[idx] = False
        self.prev_d[idx] = self._mean_dist(idx)

    def _mean_dist(self, idx=None):
        if idx is None:
            px, py, gx, gy = self.px, self.py, self.gx, self.gy
        else:
            px, py, gx, gy = self.px[idx], self.py[idx], self.gx[idx], self.gy[idx]
        d = np.sqrt((px - gx[:, None]) ** 2 + (py - gy[:, None]) ** 2)
        return d.mean(1) / self.scale

    def reset(self):
        self._reset_rows(np.arange(self.N))
        return self._obs()

    def _obs(self):
        S = self.scale; c = self.size / 2.0
        ox = (self.px - c) / c; oy = (self.py - c) / c
        visible = (self.t < self.vis_steps).astype(np.float32)  # (N,)
        gxn = ((self.gx - c) / c)[:, None] * visible[:, None]   # masque quand caché
        gyn = ((self.gy - c) / c)[:, None] * visible[:, None]
        gxn = np.broadcast_to(gxn, (self.N, self.A)); gyn = np.broadcast_to(gyn, (self.N, self.A))
        vis = np.broadcast_to(visible[:, None], (self.N, self.A))
        # plus proche coequipier
        dx = self.px[:, None, :] - self.px[:, :, None]; dy = self.py[:, None, :] - self.py[:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None], 1e18, dx * dx + dy * dy)
        jmin = d2.argmin(2)
        mdx = np.take_along_axis(dx, jmin[:, :, None], 2)[:, :, 0] / S
        mdy = np.take_along_axis(dy, jmin[:, :, None], 2)[:, :, 0] / S
        return np.stack([ox, oy, gxn, gyn, vis, mdx, mdy], axis=2).astype(np.float32)

    def step(self, actions, auto_reset=True):
        a = np.asarray(actions).astype(int)
        d = self.DELTA[a]
        moving = (self.t >= self.vis_steps).astype(np.float32)[:, None]
        self.px = np.clip(self.px + d[:, :, 0] * self.move * moving, 0, self.size)
        self.py = np.clip(self.py + d[:, :, 1] * self.move * moving, 0, self.size)
        dg = np.sqrt((self.px - self.gx[:, None]) ** 2 + (self.py - self.gy[:, None]) ** 2)
        in_goal = (dg <= self.reach_r).sum(1)
        secured = in_goal >= self.secure_n
        newly = secured & (~self.secured)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = newly.astype(np.float32) - 0.01 + shaping.astype(np.float32)
        self.secured = secured.copy()
        done_out = done.copy()
        info = {"success": secured.copy(), "in_goal": in_goal.copy()}
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return self._obs(), rew, done_out.astype(np.float32), info


if __name__ == "__main__":
    import time
    env = ToyMem(num_envs=512)
    obs = env.reset(); print("obs", obs.shape, "| visible au depart:", float(obs[0, 0, 4]))
    obs, r, d, i = env.step(np.full((512, 4), 3))
    for _ in range(4):
        obs, r, d, i = env.step(np.full((512, 4), 3))
    print("visible apres %d pas:" % 5, float(obs[0, 0, 4]), "| goal dans obs:", round(float(obs[0, 0, 2]), 3), "(0 = masque)")
    t0 = time.time()
    for _ in range(200):
        env.step(np.random.randint(0, 5, (512, 4)))
    print("debit: %.0f transitions/s" % (512 * 200 / (time.time() - t0)))
