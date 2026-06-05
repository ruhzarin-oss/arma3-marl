"""toy_selfplay — B2 SELF-PLAY : DEUX camps APPRENANTS s'affrontent pour un objectif central.
BLUFOR (A agents) vs OPFOR (A agents), chacun pilote par SA politique. Macro-actions des deux cotes
(AVANCER vers l'objectif, SUPPRESSER l'adversaire le plus proche, COUVERT). Suppression = clouer l'autre.
Victoire d'un camp : >=secure_n de ses agents dans l'objectif (et l'autre camp pas). Recompense symetrique (+1 victoire / -1 defaite).
Renvoie obs des DEUX camps -> entrainement simultane des deux politiques (co-adaptation).
obs/agent (par camp) = 10 : [ox,oy, dir_obj_x,dir_obj_y, vivant, allie_dx,allie_dy, ennemi_dx,ennemi_dy, ennemi_proche_supprime]."""
import numpy as np


class ToySelfPlay:
    def __init__(self, num_envs=512, n=3, obj_dist=140.0, move=20.0, sup_range=120.0,
                 threat_range=90.0, secure_r=30.0, secure_n=2, max_steps=30,
                 dmg_dead=0.7, hit=0.16, beta=0.25, seed=0):
        self.N = num_envs; self.A = n
        self.obj_dist = obj_dist; self.move = move; self.sup_range = sup_range; self.threat_range = threat_range
        self.secure_r = secure_r; self.secure_n = secure_n; self.max_steps = max_steps
        self.dmg_dead = dmg_dead; self.hit = hit; self.beta = beta
        self.scale = float(obj_dist); self.n_actions = 4; self.obs_dim = 10  # 0=HOLD,1=AVANCER,2=SUPPRESSER,3=COUVERT
        self.rng = np.random.default_rng(seed)
        N, A = self.N, self.A
        # camp 0 (BLU) et camp 1 (OPF), symetriques de part et d'autre de l'objectif
        self.ox = np.zeros(N); self.oy = np.zeros(N)
        self.px = np.zeros((2, N, A)); self.py = np.zeros((2, N, A)); self.dmg = np.zeros((2, N, A))
        self.supp = np.zeros((2, N, A))   # agent supprime (cloue par l'adversaire)
        self.t = np.zeros(N, dtype=int); self.prev_d = np.zeros((2, N)); self.ctrl_time = np.zeros((2, N))
        self.done_flag = np.zeros(N, dtype=bool)

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        A = self.A
        cx = self.rng.uniform(-30, 30, n); cy = self.rng.uniform(-30, 30, n)
        self.ox[idx] = cx; self.oy[idx] = cy
        # BLU a gauche, OPF a droite (symetrique)
        self.px[0][idx] = cx[:, None] - self.obj_dist + (np.arange(A)[None] % 2) * 6
        self.py[0][idx] = cy[:, None] + (np.arange(A)[None] - 1) * 8
        self.px[1][idx] = cx[:, None] + self.obj_dist - (np.arange(A)[None] % 2) * 6
        self.py[1][idx] = cy[:, None] + (np.arange(A)[None] - 1) * 8
        self.dmg[:, idx] = 0.0; self.supp[:, idx] = 0.0; self.ctrl_time[:, idx] = 0.0
        self.t[idx] = 0
        for s in range(2):
            self.prev_d[s][idx] = self._dist(s, idx)

    def _alive(self, s): return self.dmg[s] < self.dmg_dead

    def _dist(self, s, idx=None):
        if idx is None:
            px, py, al = self.px[s], self.py[s], self._alive(s)
        else:
            px, py = self.px[s][idx], self.py[s][idx]; al = (self.dmg[s][idx] < self.dmg_dead)
        d = np.sqrt((px - (self.ox[idx] if idx is not None else self.ox)[:, None]) ** 2 +
                    (py - (self.oy[idx] if idx is not None else self.oy)[:, None]) ** 2) / self.scale
        den = al.sum(1); return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self._reset_rows(np.arange(self.N))
        return self._obs(0), self._obs(1)

    def _obs(self, s):
        o = 1 - s; S = self.scale; al = self._alive(s)
        ox = (self.px[s] - self.ox[:, None]) / S; oy = (self.py[s] - self.oy[:, None]) / S
        dgx = (self.ox[:, None] - self.px[s]) / S; dgy = (self.oy[:, None] - self.py[s]) / S
        # allie le plus proche
        dx = self.px[s][:, None, :] - self.px[s][:, :, None]; dy = self.py[s][:, None, :] - self.py[s][:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, self.A, self.A)), 1e18, dx * dx + dy * dy)
        jm = d2.argmin(2)
        adx = np.take_along_axis(dx, jm[:, :, None], 2)[:, :, 0] / S; ady = np.take_along_axis(dy, jm[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
        # ennemi le plus proche (vivant)
        oal = self._alive(o)
        ex = self.px[o][:, None, :] - self.px[s][:, :, None]; ey = self.py[o][:, None, :] - self.py[s][:, :, None]
        ed2 = np.where(oal[:, None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(2)
        edx = np.take_along_axis(ex, km[:, :, None], 2)[:, :, 0] / S; edy = np.take_along_axis(ey, km[:, :, None], 2)[:, :, 0] / S
        nd = ed2.min(2) >= 1e18; edx[nd] = 0.0; edy[nd] = 0.0
        esupp = np.take_along_axis(self.supp[o], km, 1)
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, esupp], axis=2).astype(np.float32)

    def _apply(self, s, a):
        al = self._alive(s); o = 1 - s
        # SUPPRESSER (2) : clouer l'ennemi le plus proche dans sup_range
        supp_act = (a == 2) & al
        ex = self.px[o][:, :, None] - self.px[s][:, None, :]; ey = self.py[o][:, :, None] - self.py[s][:, None, :]
        within = ((ex * ex + ey * ey) <= self.sup_range ** 2) & supp_act[:, None, :]
        self.supp[o] = np.maximum(self.supp[o], within.any(2).astype(np.float32))  # marque les ennemis clouches
        # mouvement vers l'objectif (AVANCER=1, COUVERT=3 plus lent)
        tox = self.ox[:, None] - self.px[s]; toy = self.oy[:, None] - self.py[s]
        tn = np.sqrt(tox * tox + toy * toy) + 1e-6
        spd = np.zeros((self.N, self.A), dtype=np.float32); spd[a == 1] = self.move; spd[a == 3] = self.move * 0.5
        self.px[s] = self.px[s] + (tox / tn) * spd * al; self.py[s] = self.py[s] + (toy / tn) * spd * al
        return (a == 3).astype(np.float32)  # cover mask

    def step(self, a0, a1, auto_reset=True):
        self.supp[:] = 0.0
        cov0 = self._apply(0, np.asarray(a0).astype(int)); cov1 = self._apply(1, np.asarray(a1).astype(int))
        # feu : chaque agent tire sur l'ennemi le plus proche s'il n'est pas supprime (et reduit par couvert de la cible)
        for s, cov in ((0, cov1), (1, cov0)):  # s tire sur l'autre camp
            o = 1 - s; al = self._alive(s); oal = self._alive(o)
            ex = self.px[o][:, None, :] - self.px[s][:, :, None]; ey = self.py[o][:, None, :] - self.py[s][:, :, None]
            ed2 = np.where(oal[:, None, :] & (self.supp[s][:, :, None] < 0.5), ex * ex + ey * ey, 1e18)
            # s supprime ? si s clouché il ne tire pas
            nd = np.sqrt(ed2.min(2)); shoot = (self.supp[s] < 0.5).astype(np.float32) * al
            km = ed2.argmin(2)
            # degats a l'ennemi cible le plus proche
            tgt = km; exp = np.clip(1.0 - nd / self.threat_range, 0.0, 1.0) * shoot
            dmg_to = np.zeros((self.N, self.A), dtype=np.float32)
            np.add.at(dmg_to, (np.arange(self.N)[:, None], tgt), exp * self.hit)
            dmg_to = dmg_to * (1.0 - 0.6 * cov)
            self.dmg[o] = np.minimum(0.85, self.dmg[o] + dmg_to)
        self.t = self.t + 1
        # securisation
        inobj = []
        for s in range(2):
            al = self._alive(s); d2 = (self.px[s] - self.ox[:, None]) ** 2 + (self.py[s] - self.oy[:, None]) ** 2
            inobj.append(((d2 <= self.secure_r ** 2) & al).sum(1))
        sec = [inobj[0] >= self.secure_n, inobj[1] >= self.secure_n]
        self.ctrl_time[0] = self.ctrl_time[0] + inobj[0]; self.ctrl_time[1] = self.ctrl_time[1] + inobj[1]
        elim0 = ~self._alive(0).any(1); elim1 = ~self._alive(1).any(1); timeout = self.t >= self.max_steps
        win0 = (sec[0] & (~sec[1])) | elim1 | (timeout & (self.ctrl_time[0] > self.ctrl_time[1]))
        win1 = (sec[1] & (~sec[0])) | elim0 | (timeout & (self.ctrl_time[1] > self.ctrl_time[0]))
        both = win0 & win1; win0 = win0 & (~both); win1 = win1 & (~both)
        done = win0 | win1 | timeout | elim0 | elim1
        rew = [np.zeros(self.N, dtype=np.float32), np.zeros(self.N, dtype=np.float32)]
        for s in range(2):
            cur = self._dist(s); sh = self.beta * (self.prev_d[s] - cur); self.prev_d[s] = cur
            rew[s] = sh - 0.005
        ctrl = 0.04 * (inobj[0] - inobj[1]).astype(np.float32)   # king-of-the-hill : controler l'objectif rapporte
        rew[0] = rew[0] + win0.astype(np.float32) - win1.astype(np.float32) + ctrl
        rew[1] = rew[1] + win1.astype(np.float32) - win0.astype(np.float32) - ctrl
        info = {"win0": win0.copy(), "win1": win1.copy(), "decided": (win0 | win1).copy()}
        done_out = done.copy()
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return self._obs(0), self._obs(1), rew[0], rew[1], done_out.astype(np.float32), info
