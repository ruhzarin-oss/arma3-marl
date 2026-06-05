"""toy_dyn — A1 applique au COMBAT DYNAMIQUE (le V3 qui plafonnait sans memoire).
Ennemis MOBILES qui traquent l'escouade + OBS PARTIELLE : l'ennemi n'est visible que dans un rayon de vue
(edx,edy masques au-dela), il bouge -> il faut SE SOUVENIR de sa trajectoire pour l'eviter.
Combat par proximite (degats plafonnes 0.85). Recompense = +1 objectif, -0.01/pas, +shaping, -cas_pen*pertes (cout integre).
obs/agent = 10 : [ox,oy, dir_obj_x,dir_obj_y, vivant, mate_dx,mate_dy, en_dx(masque), en_dy(masque), en_vu]."""
import numpy as np


class ToyDyn:
    def __init__(self, num_envs=512, n=4, opfor=3, obj_dist=160.0, move=20.0, en_move=12.0,
                 sight=70.0, secure_r=28.0, secure_n=3, threat_range=95.0, max_steps=26,
                 dmg_dead=0.7, hit=0.14, kill=0.12, beta=0.5, cas_pen=0.3, seed=0):
        self.N = num_envs; self.A = n; self.K = opfor
        self.obj_dist = obj_dist; self.move = move; self.en_move = en_move; self.sight = sight
        self.secure_r = secure_r; self.secure_n = secure_n; self.threat_range = threat_range
        self.max_steps = max_steps; self.dmg_dead = dmg_dead; self.hit = hit; self.kill = kill
        self.beta = beta; self.cas_pen = cas_pen
        self.scale = float(obj_dist); self.n_actions = 5; self.obs_dim = 10
        self.rng = np.random.default_rng(seed)
        self.DELTA = np.array([[0, 0], [0, 1], [0, -1], [1, 0], [-1, 0]], dtype=np.float32)
        N, A, K = self.N, self.A, self.K
        self.bx = np.zeros(N); self.by = np.zeros(N); self.objx = np.zeros(N); self.objy = np.zeros(N)
        self.px = np.zeros((N, A)); self.py = np.zeros((N, A)); self.admg = np.zeros((N, A))
        self.ox = np.zeros((N, K)); self.oy = np.zeros((N, K)); self.odmg = np.zeros((N, K))
        self.t = np.zeros(N, dtype=int); self.secured = np.zeros(N, dtype=bool)
        self.prev_alive = np.full(N, A); self.prev_d = np.zeros(N)

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        A, K = self.A, self.K
        bx = self.rng.uniform(-30, 30, n); by = self.rng.uniform(-30, 30, n)
        self.bx[idx] = bx; self.by[idx] = by
        ang = self.rng.uniform(-0.4, 0.4, n)
        self.objx[idx] = bx + self.obj_dist * np.cos(ang); self.objy[idx] = by + self.obj_dist * np.sin(ang)
        self.px[idx] = bx[:, None] + (np.arange(A)[None, :] % 2) * 6 - 3
        self.py[idx] = by[:, None] + (np.arange(A)[None, :] // 2) * 6 - 3
        self.admg[idx] = 0.0
        self.ox[idx] = self.objx[idx][:, None] + (np.arange(K)[None, :] - 1) * 10
        self.oy[idx] = self.objy[idx][:, None] + (np.arange(K)[None, :] - 1) * 12
        self.odmg[idx] = 0.0
        self.t[idx] = self.rng.integers(0, self.max_steps, n)
        self.secured[idx] = False; self.prev_alive[idx] = A
        self.prev_d[idx] = self._mean_dist(idx)

    def _alive(self): return self.admg < self.dmg_dead
    def _oalive(self): return self.odmg < self.dmg_dead

    def _mean_dist(self, idx=None):
        if idx is None:
            px, py, ox, oy, al = self.px, self.py, self.objx, self.objy, self._alive()
        else:
            px, py, ox, oy = self.px[idx], self.py[idx], self.objx[idx], self.objy[idx]
            al = (self.admg[idx] < self.dmg_dead)
        d = np.sqrt((px - ox[:, None]) ** 2 + (py - oy[:, None]) ** 2) / self.scale
        den = al.sum(1)
        return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self._reset_rows(np.arange(self.N)); return self._obs()

    def _nearest_enemy(self):
        oal = self._oalive()
        tx = self.ox[:, None, :] - self.px[:, :, None]; ty = self.oy[:, None, :] - self.py[:, :, None]
        td2 = np.where(oal[:, None, :], tx * tx + ty * ty, 1e18)
        kmin = td2.argmin(2)
        ndx = np.take_along_axis(tx, kmin[:, :, None], 2)[:, :, 0]
        ndy = np.take_along_axis(ty, kmin[:, :, None], 2)[:, :, 0]
        nd = np.sqrt(np.where(td2.min(2) >= 1e18, (self.sight * 9) ** 2, td2.min(2)))
        return ndx, ndy, nd  # (N,A)

    def _obs(self):
        S = self.scale; al = self._alive()
        ox = (self.px - self.bx[:, None]) / S; oy = (self.py - self.by[:, None]) / S
        dgx = (self.objx[:, None] - self.px) / S; dgy = (self.objy[:, None] - self.py) / S
        dx = self.px[:, None, :] - self.px[:, :, None]; dy = self.py[:, None, :] - self.py[:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, self.A, self.A)),
                      1e18, dx * dx + dy * dy)
        jmin = d2.argmin(2)
        mdx = np.take_along_axis(dx, jmin[:, :, None], 2)[:, :, 0] / S
        mdy = np.take_along_axis(dy, jmin[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; mdx[nm] = 0.0; mdy[nm] = 0.0
        ndx, ndy, nd = self._nearest_enemy()
        seen = (nd <= self.sight).astype(np.float32)  # OBS PARTIELLE : ennemi visible seulement si proche
        edx = (ndx / S) * seen; edy = (ndy / S) * seen
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), mdx, mdy, edx, edy, seen], axis=2).astype(np.float32)

    def step(self, actions, auto_reset=True):
        a = np.asarray(actions).astype(int); al = self._alive()
        d = self.DELTA[a]
        self.px = self.px + d[:, :, 0] * self.move * al
        self.py = self.py + d[:, :, 1] * self.move * al
        # ennemis TRAQUENT le centroide des agents vivants
        cx = (self.px * al).sum(1) / np.maximum(al.sum(1), 1); cy = (self.py * al).sum(1) / np.maximum(al.sum(1), 1)
        oal = self._oalive()
        vx = cx[:, None] - self.ox; vy = cy[:, None] - self.oy
        vn = np.sqrt(vx * vx + vy * vy) + 1e-6
        self.ox = self.ox + (vx / vn) * self.en_move * oal
        self.oy = self.oy + (vy / vn) * self.en_move * oal
        # combat par proximite (deux sens)
        ndx, ndy, nd = self._nearest_enemy()
        a_exp = np.clip(1.0 - nd / self.threat_range, 0.0, 1.0)
        self.admg = np.minimum(0.85, self.admg + self.hit * a_exp * al)
        al2 = self._alive()
        ux = self.px[:, None, :] - self.ox[:, :, None]; uy = self.py[:, None, :] - self.oy[:, :, None]
        ud2 = np.where(al2[:, None, :], ux * ux + uy * uy, 1e18)
        o_exp = np.clip(1.0 - np.sqrt(ud2.min(2)) / self.threat_range, 0.0, 1.0)
        self.odmg = np.minimum(0.85, self.odmg + self.kill * o_exp * self._oalive())
        al = self._alive(); n_alive = al.sum(1)
        d2o = (self.px - self.objx[:, None]) ** 2 + (self.py - self.objy[:, None]) ** 2
        in_obj = ((d2o <= self.secure_r ** 2) & al).sum(1)
        secured = in_obj >= self.secure_n
        newly = secured & (~self.secured)
        cost = np.maximum(0, self.prev_alive - n_alive)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps) | (n_alive == 0)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = newly.astype(np.float32) - 0.01 + shaping.astype(np.float32) - self.cas_pen * cost.astype(np.float32)
        self.secured = secured.copy(); self.prev_alive = n_alive.astype(int)
        done_out = done.copy()
        info = {"success": secured.copy(), "alive": n_alive.copy()}
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return self._obs(), rew, done_out.astype(np.float32), info


if __name__ == "__main__":
    import time
    env = ToyDyn(num_envs=512); obs = env.reset(); print("obs", obs.shape)
    t0 = time.time()
    for _ in range(200): env.step(np.random.randint(0, 5, (512, 4)))
    print("debit: %.0f transitions/s" % (512 * 200 / (time.time() - t0)))
