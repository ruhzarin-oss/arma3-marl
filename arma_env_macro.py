"""③.1 — ArmaEnvMacro : macro-actions tactiques mappees sur de VRAIES commandes Arma.
5 macros : 0=HOLD (doStop), 1=AVANCER (doMove vers obj), 2=COUVERT (DOWN + doMove lent),
3=SUPPRESSER (doTarget+doFire l'ennemi le plus proche, et l'ennemi vise est suppressFor -> cloue),
4=ASSAUT (UP + doMove rapide). obs = 10, calee sur toy_macro : [...,en_dx_occulte, en_dy_occulte, ennemi_proche_supprime].
Sous-classe de ArmaEnvB1 (reutilise reset/_read/_spawn/_reset_zones). Combat = vraie balistique Arma."""
import time
import numpy as np
from arma_env_b1 import ArmaEnvB1


class ArmaEnvMacro(ArmaEnvB1):
    def __init__(self, num_envs=24, sup_range=120.0, **kw):
        super().__init__(num_envs=num_envs, **kw)
        self.sup_range = sup_range
        self.opf_supp = np.zeros((self.N, self.K))

    def reset(self):
        super().reset()
        self.opf_supp = np.zeros((self.N, self.K))
        return self._obs()

    def _near_enemy(self):
        tx = self.opfx[:, None, :] - self.px[:, :, None]; ty = self.opfy[:, None, :] - self.py[:, :, None]
        td2 = np.where(self.opf_alive[:, None, :], tx * tx + ty * ty, 1e18)
        kmin = td2.argmin(2)
        nox = np.take_along_axis(tx, kmin[:, :, None], 2)[:, :, 0]
        noy = np.take_along_axis(ty, kmin[:, :, None], 2)[:, :, 0]
        nd = np.sqrt(td2.min(2)); nodead = td2.min(2) >= 1e18
        return nox, noy, nd, nodead, kmin

    def _obs(self):
        S = self.scale
        basex = self.startx.mean(1, keepdims=True); basey = self.starty.mean(1, keepdims=True)
        ox = (self.px - basex) / S; oy = (self.py - basey) / S
        dgx = (self.objx[:, None] - self.px) / S; dgy = (self.objy[:, None] - self.py) / S
        al = self.alive.astype(float)
        dx = self.px[:, None, :] - self.px[:, :, None]; dy = self.py[:, None, :] - self.py[:, :, None]
        d2m = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~self.alive)[:, None, :], (self.N, self.A, self.A)), 1e18, dx * dx + dy * dy)
        jmin = d2m.argmin(2)
        mdx = np.take_along_axis(dx, jmin[:, :, None], 2)[:, :, 0] / S
        mdy = np.take_along_axis(dy, jmin[:, :, None], 2)[:, :, 0] / S
        mdx[d2m.min(2) >= 1e18] = 0.0; mdy[d2m.min(2) >= 1e18] = 0.0
        nox, noy, nd, nodead, kmin = self._near_enemy()
        seen = (nd <= self.sight) & (~nodead)
        edx = (nox / S) * seen; edy = (noy / S) * seen
        near_supp = np.take_along_axis(self.opf_supp, kmin, 1)
        return np.stack([ox, oy, dgx, dgy, al, mdx, mdy, edx, edy, near_supp], axis=2).astype(np.float32)

    def step(self, actions):
        a = np.asarray(actions).reshape(self.N, self.A).astype(int); al = self.alive
        # suppression : ennemis cloues par les agents en SUPPRESSER a portee
        sa = (a == 3) & al
        sx = self.opfx[:, :, None] - self.px[:, None, :]; sy = self.opfy[:, :, None] - self.py[:, None, :]
        within = ((sx * sx + sy * sy) <= self.sup_range ** 2) & sa[:, None, :] & self.opf_alive[:, :, None]
        self.opf_supp = within.any(2).astype(float)
        # cibles de bond (vers l'objectif) pour AVANCER/COUVERT/ASSAUT
        tox = self.objx[:, None] - self.px; toy = self.objy[:, None] - self.py
        tn = np.sqrt(tox * tox + toy * toy) + 1e-6
        spd = np.zeros((self.N, self.A)); spd[a == 1] = self.move; spd[a == 2] = self.move * 0.5; spd[a == 4] = self.move * 1.3
        tgx = self.px + (tox / tn) * spd; tgy = self.py + (toy / tn) * spd
        _, _, _, _, kmin = self._near_enemy()
        cmds = []
        for z in range(self.N):
            for i in range(self.A):
                g = z * self.A + i; m = int(a[z, i])
                if m == 0:
                    cmds.append('private _u=HMT_AG select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % g)
                elif m == 3:
                    gk = z * self.K + int(kmin[z, i])
                    cmds.append('private _u=HMT_AG select %d; private _e=HMT_OP select %d; if (!isNull _u && {alive _u} && {!isNull _e}) then {doStop _u; _u setUnitPos "UP"; _u doTarget _e; _u doFire _e;};' % (g, gk))
                else:
                    pos = "DOWN" if m == 2 else ("UP" if m == 4 else "MIDDLE")
                    cmds.append('private _u=HMT_AG select %d; if (!isNull _u && {alive _u}) then {_u setUnitPos "%s"; _u doMove [%d,%d,0];};' % (g, pos, int(tgx[z, i]), int(tgy[z, i])))
        for z in range(self.N):
            for k in range(self.K):
                if self.opf_supp[z, k] > 0.5:
                    cmds.append('private _e=HMT_OP select %d; if (!isNull _e) then {_e suppressFor 2.5;};' % (z * self.K + k))
        self.b.send("\n".join(cmds), wait=True)
        time.sleep(self.step_wait)
        self._read()
        n_alive = self.alive.sum(1)
        d2 = (self.px - self.objx[:, None]) ** 2 + (self.py - self.objy[:, None]) ** 2
        in_obj = ((d2 <= self.secure_r ** 2) & self.alive).sum(1)
        secured = in_obj >= self.secure_n; newly = secured & (~self.secured)
        cost = np.maximum(0, self.prev_alive - n_alive).astype(np.float32)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps) | (n_alive == 0)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = (newly.astype(np.float32) * 1.0) - 0.01 + shaping.astype(np.float32)
        self.secured = secured.copy(); self.prev_alive = n_alive.astype(int)
        info = {"success": secured.copy(), "in_obj": in_obj.copy(), "alive": n_alive.copy(), "opf_alive": self.opf_alive.sum(1).copy()}
        dz = np.where(done)[0]
        if len(dz) > 0:
            self._reset_zones(dz); self.opf_supp[dz] = 0.0
        return self._obs(), rew, cost, done.astype(np.float32), info
