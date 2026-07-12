#!/usr/bin/env python3
"""fast_seizehold.py — MISSION : 20 FS PRENNENT et CONSOLIDENT les ressources d'un pays defendu par 500 hommes.

Bati SUR fast_env (HARMATTAN brique 2b) : meme interface (reset / step(targets) / obs dict), meme LOS sur
heightmap (le couvert conditionne la letalite), meme QRF reactive. TROIS changements pour la mission :
  1. OBJECTIFS DISPERSES : 10 sites de ressources eparpilles (plus l'anneau de 180 m).
  2. 500 DEFENSEURS d'un coup, repartis aux sites (garnison locale) + QRF reserve -> affrontes au compte-gouttes.
  3. CONSOLIDER : `held` DYNAMIQUE -> un site repris par l'ennemi se PERD ; la defense CONTRE-ATTAQUE
     (garnison locale + QRF convergent sur les sites tenus). Victoire = tenir >= TARGET sites a la fin.
Defenseurs vectorises numpy (500 -> tractable). LOS seulement sur les paires a portee (culling).
Arma reste le juge : on bake le relief Stratis et on valide la politique pre-entrainee ensuite.
"""
import math, json, os, random
import numpy as np

N_SF = 20; N_SITES = 10; R_HOLD = 35.0
MOVE_M = 60.0; DETECT_RANGE = 350.0; FIRE_RANGE = 300.0
DEF_SKILL = 0.65; SF_SKILL = 0.75; DEF_HIT = 0.055; SF_HIT = 0.045
MAX_STEPS = 60; TARGET = 6                       # consolider >= 6/10 sites a la fin = victoire
RETAKE_RANGE = 650.0                              # une garnison < 650 m d'un site tenu va le reprendre
HM = "/home/younes/arma3-marl/raid/obj_heightmap.json"


class FastSeizeHold:
    def __init__(self, obj_center=(14038, 16143), n_per_site=40, n_qrf=100, seed=0, hm_path=HM,
                 def_hit=DEF_HIT, sf_hit=SF_HIT, target=TARGET, verbose=False):
        self.obj = obj_center; self.n_per_site = n_per_site; self.n_qrf = n_qrf
        self.def_hit = def_hit; self.sf_hit = sf_hit; self.target = target; self.verbose = verbose
        self.rng = random.Random(seed); self.nprng = np.random.default_rng(seed)
        d = json.load(open(hm_path))
        self.H = np.array(d["H"], dtype=np.float32); self.hx0 = d["x0"]; self.hy0 = d["y0"]; self.hres = d["res"]; self.hn = d["n"]
        ox, oy = obj_center
        # 10 sites DISPERSES (~ +/- 550 m, dans l'emprise du heightmap)
        offs = [(-500, 450), (400, 500), (550, -100), (-450, -400), (100, 250),
                (-200, 540), (520, 240), (-540, 50), (250, -450), (-100, -540)]
        self.subobj = [(ox + dx, oy + dy) for dx, dy in offs]
        self.qrf_home = (ox, oy - 900)            # reserve au sud
        self.n_def_total = N_SITES * n_per_site + n_qrf

    def _h(self, x, y):
        c = min(self.hn - 1, max(0, int(round((x - self.hx0) / self.hres))))
        r = min(self.hn - 1, max(0, int(round((y - self.hy0) / self.hres))))
        return float(self.H[r, c])

    def _los(self, ax, ay, bx, by, eye=1.6):
        ha = self._h(ax, ay) + eye; hb = self._h(bx, by) + eye
        dd = math.hypot(bx - ax, by - ay); steps = max(2, int(dd / self.hres))
        for k in range(1, steps):
            t = k / steps
            if self._h(ax + (bx - ax) * t, ay + (by - ay) * t) > ha + (hb - ha) * t + 0.6:
                return False
        return True

    def reset(self):
        ox, oy = self.obj
        self.sf = [[ox - 750 + self.rng.uniform(-25, 25), oy - 750 + self.rng.uniform(-25, 25), 1] for _ in range(N_SF)]
        # garnison : n_per_site autour de chaque site ; QRF : reserve au sud
        dx = []; dy = []; home = []
        for s, (sx, sy) in enumerate(self.subobj):
            for _ in range(self.n_per_site):
                dx.append(sx + self.rng.uniform(-70, 70)); dy.append(sy + self.rng.uniform(-70, 70)); home.append(s)
        qx, qy = self.qrf_home
        for _ in range(self.n_qrf):
            dx.append(qx + self.rng.uniform(-40, 40)); dy.append(qy + self.rng.uniform(-40, 40)); home.append(-1)
        self.dx = np.array(dx); self.dy = np.array(dy); self.dalive = np.ones(len(dx), bool)
        self.dhome = np.array(home); self.is_qrf = self.dhome < 0
        self.alert = 0.0; self.step_i = 0; self.held = [False] * N_SITES; self.prev_alive = N_SF; self.qrf_sent = False
        return self._pack()

    def _pack(self):
        al = self.dalive
        return {"sf": [[round(a[0]), round(a[1]), a[2]] for a in self.sf],
                "def": [[round(float(self.dx[i])), round(float(self.dy[i]))] for i in np.where(al)[0]],
                "alert": self.alert, "held": list(self.held),
                "n_alive": sum(a[2] for a in self.sf), "subobj": self.subobj}

    def step(self, actions):
        # actions : liste de N_SF = ((x,y), posture_idx)  (meme format que RaidEnv/raid_train)
        self.step_i += 1
        EXPO = {0: 1.0, 1: 0.6, 2: 0.3}; SPD = {0: 1.0, 1: 0.7, 2: 0.4}   # debout / accroupi / couche
        self.expo = [0.6] * N_SF
        # 1) deplacement SF (posture : vitesse + exposition)
        for i, a in enumerate(self.sf):
            t, post = actions[i]; self.expo[i] = EXPO.get(int(post), 0.6)
            if not a[2]: continue
            tx, ty = t; ddx, ddy = tx - a[0], ty - a[1]; dd = math.hypot(ddx, ddy) or 1
            s = min(MOVE_M, dd) * SPD.get(int(post), 0.7); a[0] += ddx / dd * s; a[1] += ddy / dd * s
        sfa = [a for a in self.sf if a[2]]
        sfx = np.array([a[0] for a in sfa]); sfy = np.array([a[1] for a in sfa])
        # 2) detection -> alerte (portee, approx : LOS sur un sous-echantillon pour la vitesse)
        detected = False
        if len(sfa):
            for i in np.where(self.dalive)[0][:: max(1, self.n_def_total // 120)]:
                rr = np.hypot(self.dx[i] - sfx, self.dy[i] - sfy)
                j = int(np.argmin(rr))
                if rr[j] < DETECT_RANGE and self._los(self.dx[i], self.dy[i], sfx[j], sfy[j]): detected = True; break
        self.alert = min(4.0, self.alert + 1.0) if detected else max(0.0, self.alert - 0.4)
        # 3) DEFENSE ACTIVE : garnison locale reprend les sites tenus (< RETAKE_RANGE) ; QRF mobilise sur les tenus
        held_pts = [self.subobj[k] for k in range(N_SITES) if self.held[k]]
        if self.alert > 1.0: self.qrf_sent = True
        if held_pts:
            hpx = np.array([p[0] for p in held_pts]); hpy = np.array([p[1] for p in held_pts])
            for i in np.where(self.dalive)[0]:
                # cible = site tenu le plus proche
                rr = np.hypot(hpx - self.dx[i], hpy - self.dy[i]); j = int(np.argmin(rr))
                local = (not self.is_qrf[i]) and rr[j] < RETAKE_RANGE
                mobile = self.is_qrf[i] and self.qrf_sent
                if local or mobile:
                    tx, ty = hpx[j], hpy[j]; ddx, ddy = tx - self.dx[i], ty - self.dy[i]; dd = math.hypot(ddx, ddy) or 1
                    s = min(MOVE_M, dd); self.dx[i] += ddx / dd * s; self.dy[i] += ddy / dd * s
        elif self.qrf_sent and len(sfa):                      # pas de site tenu mais alerte : QRF vers le centre FS
            cx, cy = float(sfx.mean()), float(sfy.mean())
            for i in np.where(self.dalive & self.is_qrf)[0]:
                ddx, ddy = cx - self.dx[i], cy - self.dy[i]; dd = math.hypot(ddx, ddy) or 1
                s = min(MOVE_M, dd); self.dx[i] += ddx / dd * s; self.dy[i] += ddy / dd * s
        # 4) COMBAT (culling par portee, LOS sur les paires a portee) — le couvert protege
        ai = np.where(self.dalive)[0]
        # defenseurs -> SF (l'EXPOSITION selon la posture module la letalite -> le couvert/se coucher protege)
        for idx, a in enumerate(self.sf):
            if not a[2]: continue
            e = self.expo[idx]
            rr = np.hypot(self.dx[ai] - a[0], self.dy[ai] - a[1]); inr = ai[rr < FIRE_RANGE]
            psurv = 1.0
            for i in inr:
                r = math.hypot(self.dx[i] - a[0], self.dy[i] - a[1])
                if self._los(self.dx[i], self.dy[i], a[0], a[1]):
                    psurv *= (1 - self.def_hit * DEF_SKILL * e * max(0.0, 1 - r / FIRE_RANGE))
            if self.nprng.random() > psurv: a[2] = 0
        # SF -> defenseurs (riposte)
        sfa2 = [a for a in self.sf if a[2]]
        for i in ai:
            psurv = 1.0
            for a in sfa2:
                r = math.hypot(self.dx[i] - a[0], self.dy[i] - a[1])
                if r < FIRE_RANGE and self._los(a[0], a[1], self.dx[i], self.dy[i]):
                    psurv *= (1 - self.sf_hit * SF_SKILL * max(0.0, 1 - r / FIRE_RANGE))
            if self.nprng.random() > psurv: self.dalive[i] = 0
        # 5) sites tenus DYNAMIQUES (se perdent si l'ennemi revient)
        prev = sum(self.held); aliveidx = np.where(self.dalive)[0]
        for k, (sx, sy) in enumerate(self.subobj):
            sfn = any(a[2] and math.hypot(a[0] - sx, a[1] - sy) < R_HOLD for a in self.sf)
            dfn = bool(np.any(np.hypot(self.dx[aliveidx] - sx, self.dy[aliveidx] - sy) < R_HOLD)) if len(aliveidx) else False
            self.held[k] = sfn and not dfn
        now = sum(self.held); n_alive = sum(a[2] for a in self.sf)
        lost = max(0, self.prev_alive - n_alive); self.prev_alive = n_alive
        r = 5.0 * (now - prev) + 0.5 * now - 5.0 * lost - 0.1
        done = False; info = {"held": now, "alive": n_alive, "alert": self.alert,
                              "def": int(self.dalive.sum()), "qrf": self.qrf_sent}
        if self.step_i >= MAX_STEPS:
            done = True; info["result"] = "VICTOIRE" if now >= self.target else ("PARTIEL" if now > 0 else "ECHEC")
            r += 100.0 if now >= self.target else 10.0 * now
        elif n_alive <= 0:
            r -= 50.0; done = True; info["result"] = "ANEANTI"
        return self._pack(), r, done, info

    def close(self): pass


if __name__ == "__main__":   # smoke : assaut scripte (chaque FS fonce sur le site le plus proche) vs 500
    import statistics as st, time
    res = {"held": [], "alive": [], "ret": []}; t0 = time.time()
    for ep in range(8):
        e = FastSeizeHold(seed=ep); ob = e.reset(); tot = 0; info = {}
        for t in range(MAX_STEPS):
            tg = []
            for a in e.sf:
                dists = [math.hypot(a[0] - s[0], a[1] - s[1]) for s in e.subobj]
                tg.append((e.subobj[int(np.argmin(dists))], 1))
            ob, rr, done, info = e.step(tg); tot += rr
            if done: break
        res["held"].append(info.get("held", 0)); res["alive"].append(info.get("alive", 0)); res["ret"].append(tot)
    print("SMOKE assaut scripte vs 500 (n=8) | defenseurs=%d" % e.n_def_total)
    print("  consolides moy = %.2f/10 (cible victoire >= %d)" % (st.mean(res["held"]), TARGET))
    print("  survivants moy = %.1f/20" % st.mean(res["alive"]))
    print("  retour moy = %.1f | %.1f s/episode" % (st.mean(res["ret"]), (time.time() - t0) / 8))
