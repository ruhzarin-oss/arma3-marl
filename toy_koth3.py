"""toy_koth3 — ETAPE A : KING OF THE HILL a TROIS camps APPRENANTS (BLU/OPF/IND).
3 factions placees a 120 deg autour d'une colline centrale contestee. Chaque camp pilote par SA politique.
L'ENNEMI d'un camp = l'UNION des deux autres (l'agent combat quiconque conteste la colline).
But du test : verifier si des COALITIONS emergent (les deux outsiders concentrent le leader) -> auto-equilibrage ~33/33/33,
au lieu d'un camp qui s'echappe (defaut du self-play 2 camps).
Macro-actions (4) : 0=HOLD, 1=AVANCER (vers colline), 2=SUPPRESSER (clouer l'ennemi le plus proche), 3=COUVERT (lent, -degats).
Recompense : controle de la colline (king-of-the-hill, symetrique) + victoire (+1 gagnant / -0.5 chacun des 2 perdants).
obs/agent = 10 : [ox,oy, dir_colline_x,dir_colline_y, vivant, allie_dx,allie_dy, ennemi_dx,ennemi_dy, ennemi_proche_supprime]."""
import numpy as np


class ToyKoth3:
    def __init__(self, num_envs=512, n=3, camps=3, obj_dist=140.0, move=20.0, sup_range=120.0,
                 threat_range=90.0, secure_r=30.0, secure_n=2, max_steps=40,
                 dmg_dead=0.7, hit=0.18, beta=0.25, kappa=0.04, tie_pen=0.0, seed=0):
        self.N = num_envs; self.A = n; self.C = camps
        self.obj_dist = obj_dist; self.move = move; self.sup_range = sup_range; self.threat_range = threat_range
        self.secure_r = secure_r; self.secure_n = secure_n; self.max_steps = max_steps
        self.dmg_dead = dmg_dead; self.hit = hit; self.beta = beta; self.kappa = kappa; self.tie_pen = tie_pen
        self.scale = float(obj_dist); self.n_actions = 4; self.obs_dim = 10
        self.rng = np.random.default_rng(seed)
        N, A, C = self.N, self.A, self.C
        self.ox = np.zeros(N); self.oy = np.zeros(N)
        self.px = np.zeros((C, N, A)); self.py = np.zeros((C, N, A)); self.dmg = np.zeros((C, N, A))
        self.supp = np.zeros((C, N, A))
        self.t = np.zeros(N, dtype=int); self.prev_d = np.zeros((C, N)); self.ctrl_time = np.zeros((C, N))

    def _others(self, s):
        return [c for c in range(self.C) if c != s]

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        A, C = self.A, self.C
        cx = self.rng.uniform(-30, 30, n); cy = self.rng.uniform(-30, 30, n)
        self.ox[idx] = cx; self.oy[idx] = cy
        for c in range(C):
            ang = 2.0 * np.pi * c / C + np.pi / 2.0
            bx = cx + self.obj_dist * np.cos(ang); by = cy + self.obj_dist * np.sin(ang)
            self.px[c][idx] = bx[:, None] + (np.arange(A)[None] % 2) * 6.0 - 3.0
            self.py[c][idx] = by[:, None] + (np.arange(A)[None] - 1) * 8.0
        self.dmg[:, idx] = 0.0; self.supp[:, idx] = 0.0; self.ctrl_time[:, idx] = 0.0
        self.t[idx] = 0
        for c in range(C):
            self.prev_d[c][idx] = self._dist(c, idx)

    def _alive(self, c): return self.dmg[c] < self.dmg_dead

    def _dist(self, c, idx=None):
        if idx is None:
            px, py, al = self.px[c], self.py[c], self._alive(c); ox, oy = self.ox, self.oy
        else:
            px, py = self.px[c][idx], self.py[c][idx]; al = (self.dmg[c][idx] < self.dmg_dead); ox, oy = self.ox[idx], self.oy[idx]
        d = np.sqrt((px - ox[:, None]) ** 2 + (py - oy[:, None]) ** 2) / self.scale
        den = al.sum(1); return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self._reset_rows(np.arange(self.N))
        return tuple(self._obs(c) for c in range(self.C))

    def _obs(self, s):
        S = self.scale; al = self._alive(s); A = self.A; others = self._others(s)
        ox = (self.px[s] - self.ox[:, None]) / S; oy = (self.py[s] - self.oy[:, None]) / S
        dgx = (self.ox[:, None] - self.px[s]) / S; dgy = (self.oy[:, None] - self.py[s]) / S
        # allie le plus proche (dans le camp s)
        dx = self.px[s][:, None, :] - self.px[s][:, :, None]; dy = self.py[s][:, None, :] - self.py[s][:, :, None]
        d2 = np.where(np.eye(A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, A, A)), 1e18, dx * dx + dy * dy)
        jm = d2.argmin(2)
        adx = np.take_along_axis(dx, jm[:, :, None], 2)[:, :, 0] / S; ady = np.take_along_axis(dy, jm[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
        # ennemi le plus proche = union des AUTRES camps
        epx = np.concatenate([self.px[o] for o in others], axis=1); epy = np.concatenate([self.py[o] for o in others], axis=1)
        eal = np.concatenate([self._alive(o) for o in others], axis=1); esp = np.concatenate([self.supp[o] for o in others], axis=1)
        ex = epx[:, None, :] - self.px[s][:, :, None]; ey = epy[:, None, :] - self.py[s][:, :, None]
        ed2 = np.where(eal[:, None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(2)
        edx = np.take_along_axis(ex, km[:, :, None], 2)[:, :, 0] / S; edy = np.take_along_axis(ey, km[:, :, None], 2)[:, :, 0] / S
        nd = ed2.min(2) >= 1e18; edx[nd] = 0.0; edy[nd] = 0.0
        esupp = np.take_along_axis(esp, km, 1)
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, esupp], axis=2).astype(np.float32)

    def _apply(self, s, a):
        al = self._alive(s); supp_act = (a == 2) & al
        for o in self._others(s):
            ex = self.px[o][:, :, None] - self.px[s][:, None, :]; ey = self.py[o][:, :, None] - self.py[s][:, None, :]
            within = ((ex * ex + ey * ey) <= self.sup_range ** 2) & supp_act[:, None, :]
            self.supp[o] = np.maximum(self.supp[o], within.any(2).astype(np.float32))
        tox = self.ox[:, None] - self.px[s]; toy = self.oy[:, None] - self.py[s]
        tn = np.sqrt(tox * tox + toy * toy) + 1e-6
        spd = np.zeros((self.N, self.A), dtype=np.float32); spd[a == 1] = self.move; spd[a == 3] = self.move * 0.5
        self.px[s] = self.px[s] + (tox / tn) * spd * al; self.py[s] = self.py[s] + (toy / tn) * spd * al
        return (a == 3).astype(np.float32)

    def step(self, acts, auto_reset=True):
        N, A, C = self.N, self.A, self.C
        self.supp[:] = 0.0
        acts = [np.asarray(a).astype(int) for a in acts]
        cov = [self._apply(s, acts[s]) for s in range(C)]
        rows = np.arange(N)[:, None]
        dmgbuf = {c: np.zeros((N, A), dtype=np.float32) for c in range(C)}
        for s in range(C):
            others = self._others(s)
            epx = np.concatenate([self.px[o] for o in others], 1); epy = np.concatenate([self.py[o] for o in others], 1)
            eal = np.concatenate([self._alive(o) for o in others], 1); ecov = np.concatenate([cov[o] for o in others], 1)
            camp_of = np.concatenate([np.full(A, o) for o in others]); loc_of = np.concatenate([np.arange(A) for o in others])
            ex = epx[:, None, :] - self.px[s][:, :, None]; ey = epy[:, None, :] - self.py[s][:, :, None]
            ed2 = np.where(eal[:, None, :], ex * ex + ey * ey, 1e18)
            shoot = (self.supp[s] < 0.5).astype(np.float32) * self._alive(s)
            km = ed2.argmin(2); nd = np.sqrt(ed2.min(2))
            exp = np.clip(1.0 - nd / self.threat_range, 0.0, 1.0) * shoot
            covt = np.take_along_axis(ecov, km, 1)
            dmgval = exp * self.hit * (1.0 - 0.6 * covt)
            tcamp = camp_of[km]; tloc = loc_of[km]
            for o in others:
                sel = (tcamp == o)
                np.add.at(dmgbuf[o], (rows, np.where(sel, tloc, 0)), dmgval * sel)
        for c in range(C):
            self.dmg[c] = np.minimum(0.85, self.dmg[c] + dmgbuf[c])
        self.t = self.t + 1
        inobj = []
        for c in range(C):
            d2 = (self.px[c] - self.ox[:, None]) ** 2 + (self.py[c] - self.oy[:, None]) ** 2
            inobj.append(((d2 <= self.secure_r ** 2) & self._alive(c)).sum(1))
            self.ctrl_time[c] = self.ctrl_time[c] + inobj[c]
        inobj_arr = np.stack(inobj)  # (C,N)
        alive_camp = np.stack([self._alive(c).any(1) for c in range(C)])  # (C,N)
        n_alive = alive_camp.sum(0)
        timeout = self.t >= self.max_steps
        # securisation : camp c a >=secure_n et tous les autres < secure_n
        sec = np.zeros((C, N), dtype=bool)
        for c in range(C):
            others_lt = np.all(np.stack([inobj[o] < self.secure_n for o in self._others(c)]), axis=0)
            sec[c] = (inobj[c] >= self.secure_n) & others_lt
        sec_any = sec.any(0)
        # vainqueur par controle cumule (strict) au timeout
        ct = self.ctrl_time; mx = ct.max(0); is_max = ct == mx; n_max = is_max.sum(0)
        ct_winner = np.where(n_max == 1, ct.argmax(0), -1)
        sole_alive = np.where(n_alive == 1, alive_camp.argmax(0), -1)
        winner = np.full(N, -1)
        for c in range(C):
            winner = np.where(sec[c], c, winner)
        winner = np.where((winner == -1) & (n_alive == 1), sole_alive, winner)
        winner = np.where((winner == -1) & timeout & (n_max == 1), ct_winner, winner)
        decided = winner >= 0
        done = sec_any | timeout | (n_alive <= 1)
        # recompenses
        rew = [np.zeros(N, dtype=np.float32) for _ in range(C)]
        mean_in = inobj_arr.sum(0)
        for c in range(C):
            cur = self._dist(c); sh = self.beta * (self.prev_d[c] - cur); self.prev_d[c] = cur
            others_in = (mean_in - inobj[c]) / max(1, C - 1)
            ctrl = self.kappa * (inobj[c] - others_in).astype(np.float32)
            wterm = np.where(winner == c, 1.0, np.where(decided, -0.5, 0.0)).astype(np.float32)
            rew[c] = sh - 0.005 + ctrl + wterm - self.tie_pen * (done & (~decided)).astype(np.float32)
        info = {"winner": winner.copy(), "decided": decided.copy(), "secured": sec_any.copy(), "occ": inobj_arr.sum(0).astype(np.float32)}
        done_out = done.copy()
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return tuple(self._obs(c) for c in range(C)), tuple(rew), done_out.astype(np.float32), info
