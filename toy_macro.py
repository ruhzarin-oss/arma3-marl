"""toy_macro — A3 MACRO-ACTIONS tactiques. La bonne SEQUENCE (suppresser -> avancer a l'abri -> assaut) gagne,
ce que les coups PRIMITIFS (juste bouger) ne peuvent pas. macro=1 : 5 macros [HOLD, AVANCER, COUVERT, SUPPRESSER, ASSAUT].
macro=0 : 5 primitifs [rester, N, S, E, O]. La SUPPRESSION cloue l'ennemi (il ne tire plus) -> les autres avancent en securite.
Combat par proximite (degats plafonnes). obs/agent = 10 : [ox,oy, dir_obj_x,dir_obj_y, vivant, mate_dx,mate_dy, en_dx,en_dy, en_supprime]."""
import numpy as np


class ToyMacro:
    def __init__(self, num_envs=512, n=4, opfor=3, obj_dist=160.0, move=22.0, macro=1,
                 sup_range=125.0, threat_range=95.0, secure_r=28.0, secure_n=3, max_steps=24,
                 dmg_dead=0.7, hit=0.20, beta=0.4, cas_pen=0.3, sight=110.0, seed=0):
        self.N = num_envs; self.A = n; self.K = opfor; self.macro = macro
        self.obj_dist = obj_dist; self.move = move; self.sup_range = sup_range; self.threat_range = threat_range
        self.secure_r = secure_r; self.secure_n = secure_n; self.max_steps = max_steps
        self.dmg_dead = dmg_dead; self.hit = hit; self.beta = beta; self.cas_pen = cas_pen; self.sight = float(sight)
        self.scale = float(obj_dist); self.n_actions = 5; self.obs_dim = 10
        self.rng = np.random.default_rng(seed)
        self.DELTA = np.array([[0, 0], [0, 1], [0, -1], [1, 0], [-1, 0]], dtype=np.float32)
        N, A, K = self.N, self.A, self.K
        self.bx = np.zeros(N); self.by = np.zeros(N); self.objx = np.zeros(N); self.objy = np.zeros(N)
        self.px = np.zeros((N, A)); self.py = np.zeros((N, A)); self.admg = np.zeros((N, A))
        self.ox = np.zeros((N, K)); self.oy = np.zeros((N, K)); self.osupp = np.zeros((N, K))
        self.t = np.zeros(N, dtype=int); self.secured = np.zeros(N, dtype=bool)
        self.prev_alive = np.full(N, A); self.prev_d = np.zeros(N)

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        A, K = self.A, self.K
        bx = self.rng.uniform(-30, 30, n); by = self.rng.uniform(-30, 30, n)
        self.bx[idx] = bx; self.by[idx] = by
        ang = self.rng.uniform(-0.3, 0.3, n)
        self.objx[idx] = bx + self.obj_dist * np.cos(ang); self.objy[idx] = by + self.obj_dist * np.sin(ang)
        self.px[idx] = bx[:, None] + (np.arange(A)[None, :] % 2) * 6 - 3
        self.py[idx] = by[:, None] + (np.arange(A)[None, :] // 2) * 6 - 3
        self.admg[idx] = 0.0
        self.ox[idx] = self.objx[idx][:, None] + (np.arange(K)[None, :] - 1) * 10
        self.oy[idx] = self.objy[idx][:, None] + (np.arange(K)[None, :] - 1) * 12
        self.osupp[idx] = 0.0
        self.t[idx] = self.rng.integers(0, self.max_steps, n)
        self.secured[idx] = False; self.prev_alive[idx] = A; self.prev_d[idx] = self._mean_dist(idx)

    def _alive(self): return self.admg < self.dmg_dead

    def _mean_dist(self, idx=None):
        if idx is None:
            px, py, ox, oy, al = self.px, self.py, self.objx, self.objy, self._alive()
        else:
            px, py, ox, oy = self.px[idx], self.py[idx], self.objx[idx], self.objy[idx]; al = (self.admg[idx] < self.dmg_dead)
        d = np.sqrt((px - ox[:, None]) ** 2 + (py - oy[:, None]) ** 2) / self.scale
        den = al.sum(1)
        return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self._reset_rows(np.arange(self.N)); return self._obs()

    def _nearest_enemy(self):
        ex = self.ox[:, None, :] - self.px[:, :, None]; ey = self.oy[:, None, :] - self.py[:, :, None]
        ed2 = ex * ex + ey * ey; kn = ed2.argmin(2)
        edx = np.take_along_axis(ex, kn[:, :, None], 2)[:, :, 0]; edy = np.take_along_axis(ey, kn[:, :, None], 2)[:, :, 0]
        nd = np.sqrt(ed2.min(2)); nsupp = np.take_along_axis(self.osupp, kn, 1)
        return edx, edy, nd, nsupp

    def _obs(self):
        S = self.scale; al = self._alive()
        ox = (self.px - self.bx[:, None]) / S; oy = (self.py - self.by[:, None]) / S
        dgx = (self.objx[:, None] - self.px) / S; dgy = (self.objy[:, None] - self.py) / S
        dx = self.px[:, None, :] - self.px[:, :, None]; dy = self.py[:, None, :] - self.py[:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, self.A, self.A)), 1e18, dx * dx + dy * dy)
        jmin = d2.argmin(2)
        mdx = np.take_along_axis(dx, jmin[:, :, None], 2)[:, :, 0] / S; mdy = np.take_along_axis(dy, jmin[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; mdx[nm] = 0.0; mdy[nm] = 0.0
        edx, edy, nd, nsupp = self._nearest_enemy()
        seen = (nd <= self.sight).astype(np.float32)
        edx = edx * seen; edy = edy * seen
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), mdx, mdy, edx / S, edy / S, nsupp], axis=2).astype(np.float32)

    def step(self, actions, auto_reset=True):
        a = np.asarray(actions).astype(int); al = self._alive()
        if self.macro:
            supp_act = (a == 3) & al                                   # SUPPRESSER
            ex = self.ox[:, :, None] - self.px[:, None, :]; ey = self.oy[:, :, None] - self.py[:, None, :]
            ed2 = ex * ex + ey * ey
            within = (ed2 <= self.sup_range ** 2) & supp_act[:, None, :]
            self.osupp = within.any(2).astype(np.float32)              # ennemi cloue ce pas
            tox = self.objx[:, None] - self.px; toy = self.objy[:, None] - self.py
            tn = np.sqrt(tox * tox + toy * toy) + 1e-6
            spd = np.zeros((self.N, self.A), dtype=np.float32)
            spd[a == 1] = self.move; spd[a == 2] = self.move * 0.5; spd[a == 4] = self.move * 1.3   # AVANCER/COUVERT/ASSAUT
            self.px = self.px + (tox / tn) * spd * al; self.py = self.py + (toy / tn) * spd * al
            cover = (a == 2).astype(np.float32)                        # COUVERT reduit l'exposition
        else:
            d = self.DELTA[a]
            self.px = self.px + d[:, :, 0] * self.move * al; self.py = self.py + d[:, :, 1] * self.move * al
            self.osupp = np.zeros((self.N, self.K), dtype=np.float32)  # primitifs : pas de suppression
            cover = np.zeros((self.N, self.A), dtype=np.float32)
        # feu ennemi : seuls les ennemis NON supprimes tirent
        edx, edy, nd, nsupp = self._nearest_enemy()
        exposure = np.clip(1.0 - nd / self.threat_range, 0.0, 1.0) * (1.0 - nsupp) * (1.0 - 0.6 * cover)
        self.admg = np.minimum(0.85, self.admg + self.hit * exposure * al)
        al = self._alive(); n_alive = al.sum(1)
        d2o = (self.px - self.objx[:, None]) ** 2 + (self.py - self.objy[:, None]) ** 2
        secured = ((d2o <= self.secure_r ** 2) & al).sum(1) >= self.secure_n
        newly = secured & (~self.secured)
        cost = np.maximum(0, self.prev_alive - n_alive)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps) | (n_alive == 0)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = newly.astype(np.float32) - 0.01 + shaping.astype(np.float32) - self.cas_pen * cost.astype(np.float32)
        self.secured = secured.copy(); self.prev_alive = n_alive.astype(int); done_out = done.copy()
        info = {"success": secured.copy(), "alive": n_alive.copy()}
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return self._obs(), rew, done_out.astype(np.float32), info
