"""toy_both — exige MEMOIRE *et* COMMUNICATION. Seul l'agent 0 (eclaireur) voit l'objectif,
et SEULEMENT pendant les premiers pas (agent fige), puis CACHE pour TOUS. Les 3 autres ne le voient JAMAIS.
Il faut >=3 agents a l'objectif -> l'eclaireur doit SE SOUVENIR (memoire) ET DIFFUSER (comms) ;
les aveugles RECOIVENT + naviguent. Sans memoire = l'eclaireur oublie ; sans comms = les aveugles errent.
obs/agent = 6 : [own_x, own_y, goal_x, goal_y, est_eclaireur, visible]."""
import numpy as np


class ToyBoth:
    def __init__(self, num_envs=512, n=4, size=12.0, move=1.0, reach_r=1.7, secure_n=3,
                 vis_steps=2, max_steps=24, beta=0.3, seed=0):
        self.N = num_envs; self.A = n; self.size = size; self.move = move
        self.reach_r = reach_r; self.secure_n = secure_n; self.vis_steps = vis_steps
        self.max_steps = max_steps; self.beta = beta
        self.obs_dim = 6; self.n_actions = 5; self.scale = size
        self.rng = np.random.default_rng(seed)
        self.DELTA = np.array([[0, 0], [0, 1], [0, -1], [1, 0], [-1, 0]], dtype=np.float32)
        self.px = np.zeros((self.N, self.A)); self.py = np.zeros((self.N, self.A))
        self.gx = np.zeros(self.N); self.gy = np.zeros(self.N)
        self.t = np.zeros(self.N, dtype=int); self.secured = np.zeros(self.N, dtype=bool); self.prev_d = np.zeros(self.N)

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        c = self.size / 2.0
        self.px[idx] = c + self.rng.uniform(-1.5, 1.5, (n, self.A))
        self.py[idx] = c + self.rng.uniform(-1.5, 1.5, (n, self.A))
        ang = self.rng.uniform(0, 2 * np.pi, n); rad = self.rng.uniform(0.55, 0.8, n) * (self.size / 2)
        self.gx[idx] = c + rad * np.cos(ang); self.gy[idx] = c + rad * np.sin(ang)
        self.t[idx] = 0; self.secured[idx] = False; self.prev_d[idx] = self._mean_dist(idx)

    def _mean_dist(self, idx=None):
        if idx is None:
            px, py, gx, gy = self.px, self.py, self.gx, self.gy
        else:
            px, py, gx, gy = self.px[idx], self.py[idx], self.gx[idx], self.gy[idx]
        return np.sqrt((px - gx[:, None]) ** 2 + (py - gy[:, None]) ** 2).mean(1) / self.scale

    def reset(self):
        self._reset_rows(np.arange(self.N)); return self._obs()

    def _obs(self):
        c = self.size / 2.0
        ox = (self.px - c) / c; oy = (self.py - c) / c
        scout = np.zeros((self.N, self.A), dtype=np.float32); scout[:, 0] = 1.0
        vis = (self.t < self.vis_steps).astype(np.float32)[:, None]               # visible que les 1ers pas
        show = scout * vis                                                        # eclaireur ET visible
        gxn = (((self.gx - c) / c)[:, None]) * show
        gyn = (((self.gy - c) / c)[:, None]) * show
        visf = np.broadcast_to(vis, (self.N, self.A))
        return np.stack([ox, oy, gxn, gyn, scout, visf], axis=2).astype(np.float32)

    def step(self, actions, auto_reset=True):
        a = np.asarray(actions).astype(int); d = self.DELTA[a]
        moving = (self.t >= self.vis_steps).astype(np.float32)[:, None]           # fige pendant la phase visible
        self.px = np.clip(self.px + d[:, :, 0] * self.move * moving, 0, self.size)
        self.py = np.clip(self.py + d[:, :, 1] * self.move * moving, 0, self.size)
        dg = np.sqrt((self.px - self.gx[:, None]) ** 2 + (self.py - self.gy[:, None]) ** 2)
        secured = (dg <= self.reach_r).sum(1) >= self.secure_n
        newly = secured & (~self.secured)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = newly.astype(np.float32) - 0.01 + shaping.astype(np.float32)
        self.secured = secured.copy(); done_out = done.copy()
        info = {"success": secured.copy()}
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return self._obs(), rew, done_out.astype(np.float32), info
