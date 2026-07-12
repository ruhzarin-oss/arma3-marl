#!/usr/bin/env python3
"""fast_env.py — ENV RAPIDE FIDELE pour le pre-entrainement hybride (HARMATTAN, Brique 2b).
Meme interface que RaidEnv (reset / step(targets) / obs dict) mais simule en Python -> milliers d'episodes/min.
FIDELITE : LOS sur heightmap FIN d'Altis (obj_heightmap.json) -> la couverture terrain CONDITIONNE la letalite
(= le mecanisme du defile/couverture qu'on veut faire emerger) ; dispositif defensif reel ; FSM d'alerte ; QRF reactive.
Arma reste le juge : on finetune/valide la politique pre-entrainee ici sur Arma reel ensuite."""
import math, json, os, random
import numpy as np

N_SF = 20; N_SUBOBJ = 10; R_HOLD = 35.0
MOVE_M = 60.0                 # m/pas (cale sur Arma)
DETECT_RANGE = 350.0; FIRE_RANGE = 300.0
DEF_SKILL = 0.65; SF_SKILL = 0.75
DEF_HIT = 0.055; SF_HIT = 0.045
MAX_STEPS = 40
HM = "/home/younes/arma3-marl/raid/obj_heightmap.json"

class FastRaidEnv:
    def __init__(self, slot=0, obj_center=(14038, 16143), n_def=30, n_qrf=14, seed=0, hm_path=HM, verbose=False,
                 def_hit=DEF_HIT, sf_hit=SF_HIT):
        self.obj = obj_center; self.n_def = n_def; self.n_qrf = n_qrf
        self.def_hit = def_hit; self.sf_hit = sf_hit
        self.rng = random.Random(seed); self.nprng = np.random.default_rng(seed); self.verbose = verbose
        d = json.load(open(hm_path))
        self.H = np.array(d["H"], dtype=np.float32); self.hx0 = d["x0"]; self.hy0 = d["y0"]; self.hres = d["res"]; self.hn = d["n"]
        self.subobj = [(obj_center[0] + 180 * math.cos(2 * math.pi * i / N_SUBOBJ),
                        obj_center[1] + 180 * math.sin(2 * math.pi * i / N_SUBOBJ)) for i in range(N_SUBOBJ)]
        self.insertion = (obj_center[0] - 650, obj_center[1] - 650)
        self.qrf_pos = (obj_center[0] + 900, obj_center[1] + 900)

    def _h(self, x, y):
        c = int(round((x - self.hx0) / self.hres)); r = int(round((y - self.hy0) / self.hres))
        c = min(self.hn - 1, max(0, c)); r = min(self.hn - 1, max(0, r))
        return float(self.H[r, c])
    def _los(self, ax, ay, bx, by, eye=1.6):
        ha = self._h(ax, ay) + eye; hb = self._h(bx, by) + eye
        d = math.hypot(bx - ax, by - ay)
        steps = max(2, int(d / self.hres))
        for k in range(1, steps):
            t = k / steps
            if self._h(ax + (bx - ax) * t, ay + (by - ay) * t) > ha + (hb - ha) * t + 0.6: return False
        return True

    def reset(self):
        ox, oy = self.obj; ix, iy = self.insertion; qx, qy = self.qrf_pos
        self.sf = [[ix + self.rng.uniform(-20, 20), iy + self.rng.uniform(-20, 20), 1] for _ in range(N_SF)]
        gar = [[ox + self.rng.uniform(-80, 80), oy + self.rng.uniform(-80, 80)] for _ in range(self.n_def)]
        qrf = [[qx + self.rng.uniform(-15, 15), qy + self.rng.uniform(-15, 15)] for _ in range(self.n_qrf)]
        self.df = [d + [1] for d in gar + qrf]            # [x,y,alive]
        self.n_garr = self.n_def
        self.alert = 0.0; self.step_i = 0; self.held = [False] * N_SUBOBJ; self.prev_alive = N_SF; self.qrf_sent = False
        return self._pack()
    def _pack(self):
        return {"sf": [[round(a[0]), round(a[1]), a[2]] for a in self.sf],
                "def": [[round(d[0]), round(d[1])] for d in self.df if d[2]],
                "alert": self.alert, "held": list(self.held),
                "n_alive": sum(a[2] for a in self.sf), "subobj": self.subobj}

    def step(self, targets):
        self.step_i += 1
        # 1) deplacement SF
        for i, a in enumerate(self.sf):
            if not a[2]: continue
            tx, ty = targets[i]; dx, dy = tx - a[0], ty - a[1]; dd = math.hypot(dx, dy) or 1
            s = min(MOVE_M, dd); a[0] += dx / dd * s; a[1] += dy / dd * s
        # 2) detection -> alerte (LOS + portee) ; QRF reactive
        detected = False
        for d in self.df:
            if not d[2]: continue
            for a in self.sf:
                if a[2] and math.hypot(d[0] - a[0], d[1] - a[1]) < DETECT_RANGE and self._los(d[0], d[1], a[0], a[1]):
                    detected = True; break
            if detected: break
        self.alert = min(4.0, self.alert + 1.0) if detected else max(0.0, self.alert - 0.4)
        alive_sf = [a for a in self.sf if a[2]]
        if self.alert > 1.0 and not self.qrf_sent and alive_sf:
            cx = sum(a[0] for a in alive_sf) / len(alive_sf); cy = sum(a[1] for a in alive_sf) / len(alive_sf)
            for d in self.df[self.n_garr:]: d.append(0); d[3:] = [cx, cy]      # marque QRF en mouvement vers (cx,cy)
            self.qrf_sent = True
        # QRF avance vers sa cible
        if self.qrf_sent:
            for d in self.df[self.n_garr:]:
                if not d[2] or len(d) < 6: continue
                tx, ty = d[4], d[5]; dx, dy = tx - d[0], ty - d[1]; dd = math.hypot(dx, dy) or 1
                s = min(MOVE_M, dd); d[0] += dx / dd * s; d[1] += dy / dd * s
        # 3) combat : seules les paires AVEC LOS + portee echangent le feu (la couverture protege)
        # defenseurs -> SF
        for a in self.sf:
            if not a[2]: continue
            psurv = 1.0
            for d in self.df:
                if not d[2]: continue
                r = math.hypot(d[0] - a[0], d[1] - a[1])
                if r < FIRE_RANGE and self._los(d[0], d[1], a[0], a[1]):
                    psurv *= (1 - self.def_hit * DEF_SKILL * max(0.0, 1 - r / FIRE_RANGE))
            if self.nprng.random() > psurv: a[2] = 0
        # SF -> defenseurs (riposte : attrition de la defense)
        for d in self.df:
            if not d[2]: continue
            psurv = 1.0
            for a in self.sf:
                if not a[2]: continue
                r = math.hypot(d[0] - a[0], d[1] - a[1])
                if r < FIRE_RANGE and self._los(a[0], a[1], d[0], d[1]):
                    psurv *= (1 - self.sf_hit * SF_SKILL * max(0.0, 1 - r / FIRE_RANGE))
            if self.nprng.random() > psurv: d[2] = 0
        # 4) sous-objectifs tenus
        prev = sum(self.held)
        for k, (sx, sy) in enumerate(self.subobj):
            sfn = any(a[2] and math.hypot(a[0] - sx, a[1] - sy) < R_HOLD for a in self.sf)
            dfn = any(d[2] and math.hypot(d[0] - sx, d[1] - sy) < R_HOLD for d in self.df)
            if sfn and not dfn: self.held[k] = True
        now = sum(self.held); n_alive = sum(a[2] for a in self.sf)
        lost = max(0, self.prev_alive - n_alive); self.prev_alive = n_alive
        r = 10.0 * (now - prev) - 0.1 - 5.0 * lost
        done = False; info = {"held": now, "alive": n_alive, "alert": self.alert, "def": sum(d[2] for d in self.df), "qrf": self.qrf_sent}
        if now >= N_SUBOBJ: r += 100; done = True; info["result"] = "VICTOIRE"
        elif n_alive <= 0: r -= 50; done = True; info["result"] = "ANEANTI"
        elif self.step_i >= MAX_STEPS: done = True; info["result"] = "TEMPS"
        return self._pack(), r, done, info
    def close(self): pass

if __name__ == "__main__":
    # CALIBRATION : l'assaut scripte doit donner des chiffres proches d'Arma (~1/10 tenus, ~8/20 survivants)
    import statistics as st
    res = {"held": [], "alive": [], "ret": []}
    for ep in range(40):
        e = FastRaidEnv(seed=ep); e.reset(); tot = 0; info = {}
        for t in range(MAX_STEPS):
            tg = [e.subobj[i % N_SUBOBJ] for i in range(N_SF)]
            _, rr, done, info = e.step(tg); tot += rr
            if done: break
        res["held"].append(info.get("held", 0)); res["alive"].append(info.get("alive", 0)); res["ret"].append(tot)
    print("CALIBRATION assaut scripte (n=40 sur FastRaidEnv) :", flush=True)
    print("  tenus     moy=%.2f/10" % st.mean(res["held"]), flush=True)
    print("  survivants moy=%.1f/20" % st.mean(res["alive"]), flush=True)
    print("  retour    moy=%.1f" % st.mean(res["ret"]), flush=True)
    print("  (cible Arma : ~1/10 tenus, ~8/20 survivants, retour ~ -54)", flush=True)
    print("CALIB_DONE", flush=True)
