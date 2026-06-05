"""toy_koth3v2 — ETAPE A v2 : KotH 3 camps avec COALITION INCITEE.
Trois changements vs v1 :
 (1) SIGNAL DE LEADER dans l'obs (obs 12) : direction vers l'agent le plus proche du CAMP ADVERSE qui mene
     (plus grande duree de controle cumulee) -> l'agent PEUT viser deliberement le plus fort.
 (2) RECOMPENSE pour DELOGER le leader : bonus = focus * degats infliges par mon camp au leader -> coalition INCITEE.
 (3) (cote trainer) init identique des 3 reseaux -> separe la 'chance d'init' de la vraie dynamique.
obs/agent = 12 : [...10 de v1..., leader_dx, leader_dy]."""
import numpy as np
from toy_koth3 import ToyKoth3


class ToyKoth3V2(ToyKoth3):
    def __init__(self, *args, focus=1.5, **kw):
        super().__init__(*args, **kw)
        self.obs_dim = 12
        self.focus = focus

    def _lead_camp(self, s):
        others = self._others(s)
        cto = np.stack([self.ctrl_time[o] for o in others])  # (C-1, N)
        lead_local = cto.argmax(0)
        return np.array(others)[lead_local]  # (N,)

    def _obs(self, s):
        base = super()._obs(s)  # (N,A,10)
        S = self.scale; N, A = self.N, self.A
        lead_camp = self._lead_camp(s); idxN = np.arange(N)
        lpx = self.px[lead_camp, idxN]; lpy = self.py[lead_camp, idxN]
        lal = self.dmg[lead_camp, idxN] < self.dmg_dead
        ex = lpx[:, None, :] - self.px[s][:, :, None]; ey = lpy[:, None, :] - self.py[s][:, :, None]
        ed2 = np.where(lal[:, None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(2)
        ldx = np.take_along_axis(ex, km[:, :, None], 2)[:, :, 0] / S
        ldy = np.take_along_axis(ey, km[:, :, None], 2)[:, :, 0] / S
        nd = ed2.min(2) >= 1e18; ldx[nd] = 0.0; ldy[nd] = 0.0
        lead = np.stack([ldx, ldy], axis=2).astype(np.float32)
        return np.concatenate([base, lead], axis=2)

    def step(self, acts, auto_reset=True):
        N, A, C = self.N, self.A, self.C
        self.supp[:] = 0.0
        acts = [np.asarray(a).astype(int) for a in acts]
        cov = [self._apply(s, acts[s]) for s in range(C)]
        rows = np.arange(N)[:, None]
        dmgbuf = {c: np.zeros((N, A), dtype=np.float32) for c in range(C)}
        dmg_by = np.zeros((C, C, N), dtype=np.float32)
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
                dmg_by[s, o] = (dmgval * sel).sum(1)
        for c in range(C):
            self.dmg[c] = np.minimum(0.85, self.dmg[c] + dmgbuf[c])
        self.t = self.t + 1
        inobj = []
        for c in range(C):
            d2 = (self.px[c] - self.ox[:, None]) ** 2 + (self.py[c] - self.oy[:, None]) ** 2
            inobj.append(((d2 <= self.secure_r ** 2) & self._alive(c)).sum(1))
            self.ctrl_time[c] = self.ctrl_time[c] + inobj[c]
        inobj_arr = np.stack(inobj)
        alive_camp = np.stack([self._alive(c).any(1) for c in range(C)])
        n_alive = alive_camp.sum(0)
        timeout = self.t >= self.max_steps
        sec = np.zeros((C, N), dtype=bool)
        for c in range(C):
            others_lt = np.all(np.stack([inobj[o] < self.secure_n for o in self._others(c)]), axis=0)
            sec[c] = (inobj[c] >= self.secure_n) & others_lt
        sec_any = sec.any(0)
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
        leader = ct.argmax(0); idxN = np.arange(N)
        rew = [np.zeros(N, dtype=np.float32) for _ in range(C)]
        mean_in = inobj_arr.sum(0)
        for c in range(C):
            cur = self._dist(c); sh = self.beta * (self.prev_d[c] - cur); self.prev_d[c] = cur
            others_in = (mean_in - inobj[c]) / max(1, C - 1)
            ctrl = self.kappa * (inobj[c] - others_in).astype(np.float32)
            wterm = np.where(winner == c, 1.0, np.where(decided, -0.5, 0.0)).astype(np.float32)
            fb = self.focus * dmg_by[c, leader, idxN]
            fb = np.where(leader != c, fb, 0.0).astype(np.float32)
            rew[c] = sh - 0.005 + ctrl + wterm + fb
        info = {"winner": winner.copy(), "decided": decided.copy()}
        done_out = done.copy()
        if auto_reset:
            self._reset_rows(np.where(done)[0])
        return tuple(self._obs(c) for c in range(C)), tuple(rew), done_out.astype(np.float32), info
