"""COMMANDER+DRONE ENV — incrément "le commandant ALLOUE un drone de reco" (capacité déléguée, décision apprise).

Différence avec commander_env.py :
- OBSERVATION PARTIELLE (fog avec mémoire). Le commandant ne voit plus les défenseurs en clair.
  Chaque défenseur a une CROYANCE = (derniere position connue, age). Sources de révélation :
    * CONTACT : un fantassin vivant a moins de contact_r du défenseur.
    * DRONE   : le défenseur est sous le rayon capteur du drone (vue aérienne, sans LOS).
  Au-delà de forget_T pas sans revoir -> la croyance est OUBLIEE (inconnue).
- ACTION = K positions d'element (comme avant) + 1 position cible du DRONE -> (N, K+1, 2) dans [-1,1].
  Le drone se déplace à VITESSE FINIE vers sa cible (la conduite/le vol = délégués, pas appris).
- Le bas-niveau (réflexe de tir) garde la VERITE locale : le soldat voit/tire le défenseur proche en LOS.
  Le FOG est au niveau COMMANDEMENT (planification), pas au niveau réflexe.

baseline A/B : drone_r=0.0 -> le drone ne révèle rien (fog pur). Même obs/act dims -> même réseau -> comparaison propre.
"""
import torch, math
from assault_terrain import AssaultTerrain
import terrain_gpu as TG


class CommanderDroneEnv:
    def __init__(self, num_envs, A=8, K=2, D=8, device="cuda:0", seed=0, t_low=8, R_place=95.0,
                 max_steps=96, fire_range=110.0, secure_r=22.0, relief=35.0,
                 drone_r=70.0, contact_r=55.0, forget_T=4, drone_speed=60.0, R_drone=150.0,
                 reveal_bonus=0.05):
        self.body = AssaultTerrain(num_envs=num_envs, A=A, D=D, device=device, seed=seed, shell_obs=False,
                                   team_obs=False, suffer=False, relief=relief, fire_range=fire_range,
                                   secure_r=secure_r, max_steps=max_steps)
        self.N = num_envs; self.A = A; self.K = K; self.D = D; self.dev = device
        self.t_low = t_low; self.R_place = R_place; self.S = self.body.scale; self.fire_range = fire_range
        self.secure_r = secure_r; self.maxT = max(1, max_steps // t_low)
        # fog / drone
        self.drone_r = drone_r; self.contact_r = contact_r; self.forget_T = float(forget_T)
        self.drone_speed = drone_speed; self.R_drone = R_drone; self.reveal_bonus = reveal_bonus
        per = A // K
        self.elem = torch.arange(A, device=device) // per
        self.elem = self.elem.clamp(max=K - 1)
        self.obs_dim = 7 * K + 7        # +4 globals drone/fog par rapport a 7K+3
        self.act_dim = (K + 1) * 2      # K elements + 1 drone
        self.t_hi = torch.zeros(num_envs, dtype=torch.long, device=device)
        self._prevmin = torch.zeros(num_envs, device=device)
        self._bestmin = torch.zeros(num_envs, device=device)
        self._prevdk = torch.zeros(num_envs, device=device)
        self._prevalive = torch.zeros(num_envs, device=device)
        # croyance (fog avec memoire)
        self.bel_x = torch.zeros(num_envs, D, device=device)
        self.bel_y = torch.zeros(num_envs, D, device=device)
        self.bel_age = torch.full((num_envs, D), self.forget_T + 10.0, device=device)
        self.bel_known = torch.zeros(num_envs, D, dtype=torch.bool, device=device)
        self.drone_x = torch.zeros(num_envs, device=device)
        self.drone_y = torch.zeros(num_envs, device=device)

    # ---- elements ----
    def _emask(self, k):
        return (self.elem == k).unsqueeze(0) & self.body._aalive()

    def _elem_centroid(self, k):
        m = self._emask(k).float()
        w = m / m.sum(1, keepdim=True).clamp(min=1)
        cx = (self.body.apx * w).sum(1); cy = (self.body.apy * w).sum(1)
        return torch.stack([cx, cy], dim=1)

    # ---- VERITE (utilisée par le réflexe bas-niveau seulement) ----
    def _nearest_def(self, px, py):
        ex = self.body.dpx.unsqueeze(1) - px.unsqueeze(2)
        ey = self.body.dpy.unsqueeze(1) - py.unsqueeze(2)
        BIG = torch.tensor(1e18, device=self.dev)
        d2 = torch.where(self.body._dalive().unsqueeze(1), ex * ex + ey * ey, BIG)
        j = d2.argmin(2)
        bx = torch.gather(self.body.dpx, 1, j); by = torch.gather(self.body.dpy, 1, j)
        dx = bx - px; dy = by - py; dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
        return dx, dy, dist

    # ---- CROYANCE (utilisée par l'obs du commandant) ----
    def _nearest_bel(self, px, py):                    # px,py (N,1) -> dx,dy,dist (N,1), anyknown (N,)
        known = self.bel_known & self.body._dalive()   # ne croit qu'aux vivants connus
        ex = self.bel_x.unsqueeze(1) - px.unsqueeze(2)
        ey = self.bel_y.unsqueeze(1) - py.unsqueeze(2)
        BIG = torch.tensor(1e18, device=self.dev)
        d2 = torch.where(known.unsqueeze(1), ex * ex + ey * ey, BIG)
        j = d2.argmin(2)
        bx = torch.gather(self.bel_x, 1, j); by = torch.gather(self.bel_y, 1, j)
        dx = bx - px; dy = by - py; dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
        return dx, dy, dist, known.any(1)

    def _min_obj_dist(self):
        d = torch.sqrt(self.body.apx ** 2 + self.body.apy ** 2)
        d = torch.where(self.body._aalive(), d, torch.tensor(1e9, device=self.dev))
        return d.min(1).values

    def _cover_at(self, px, py):
        return TG.sample(self.body.cover, px, py, self.S).clamp(max=1.0)

    def _obs(self):
        S = self.S; parts = []
        for k in range(self.K):
            c = self._elem_centroid(k)
            al = self._emask(k).float().sum(1) / max(1, (self.elem == k).sum().item())
            covv = self._cover_at(c[:, 0:1], c[:, 1:2]).squeeze(1)
            dx, dy, dist, anyk = self._nearest_bel(c[:, 0:1], c[:, 1:2])
            distc = dist.squeeze(1)
            ux = torch.where(anyk, dx.squeeze(1) / distc, torch.zeros_like(distc))
            uy = torch.where(anyk, dy.squeeze(1) / distc, torch.zeros_like(distc))
            dfeat = torch.where(anyk, (distc / S).clamp(max=2), torch.full_like(distc, 2.0))
            parts.append(torch.stack([c[:, 0] / S, c[:, 1] / S, al, covv, ux, uy, dfeat], dim=1))
        # globals : ennemis vivants, amis vivants, temps, + drone x/y, frac connue, vetuste moyenne
        known_alive = (self.bel_known & self.body._dalive()).float().sum(1) / self.D
        kf = self.bel_known.float()
        mean_age = (self.bel_age * kf).sum(1) / kf.sum(1).clamp(min=1)
        g = torch.stack([self.body._dalive().float().sum(1) / self.D,
                         self.body._aalive().float().sum(1) / self.A,
                         self.t_hi.float() / self.maxT,
                         self.drone_x / S, self.drone_y / S,
                         known_alive, (mean_age / self.forget_T).clamp(max=1.0)], dim=1)
        return torch.cat(parts + [g], dim=1)           # (N, 7K+7)

    def _drone_init(self, idx=None):                   # drone démarre au centroïde ami (sud)
        aal = self.body._aalive().float()
        w = aal / aal.sum(1, keepdim=True).clamp(min=1)
        cx = (self.body.apx * w).sum(1); cy = (self.body.apy * w).sum(1)
        if idx is None:
            self.drone_x = cx.clone(); self.drone_y = cy.clone()
        else:
            self.drone_x[idx] = cx[idx]; self.drone_y[idx] = cy[idx]

    def _update_belief(self):                          # -> (N,) nb de défenseurs nouvellement révélés
        dal = self.body._dalive()
        apx, apy = self.body.apx, self.body.apy
        aal = self.body._aalive()
        ex = self.body.dpx.unsqueeze(1) - apx.unsqueeze(2)     # (N,A,D)
        ey = self.body.dpy.unsqueeze(1) - apy.unsqueeze(2)
        contact = (((ex * ex + ey * ey) < self.contact_r ** 2) & aal.unsqueeze(2)).any(1)   # (N,D)
        ddx = self.body.dpx - self.drone_x.unsqueeze(1)
        ddy = self.body.dpy - self.drone_y.unsqueeze(1)
        seen_drone = (ddx * ddx + ddy * ddy) < (self.drone_r ** 2)                          # (N,D)
        observed = (contact | seen_drone) & dal                                             # (N,D)
        self.bel_x = torch.where(observed, self.body.dpx, self.bel_x)
        self.bel_y = torch.where(observed, self.body.dpy, self.bel_y)
        self.bel_age = torch.where(observed, torch.zeros_like(self.bel_age), self.bel_age + 1.0)
        newly = observed & (~self.bel_known)
        self.bel_known = (self.bel_known | observed) & dal & (self.bel_age <= self.forget_T)
        return newly.float().sum(1)

    def reset(self):
        self.body._reset(torch.arange(self.N, device=self.dev))
        self.t_hi[:] = 0
        self.bel_known[:] = False; self.bel_age[:] = self.forget_T + 10.0
        self.bel_x[:] = 0.0; self.bel_y[:] = 0.0
        self._drone_init()
        self._update_belief()
        self._prevmin = self._min_obj_dist() / self.S
        self._bestmin = self._prevmin.clone()
        self._prevdk = (self.body.ddmg >= self.body.dmg_dead).float().sum(1)
        self._prevalive = self.body._aalive().float().sum(1)
        return self._obs()

    def _lowlevel(self, targets):                      # réflexe : VERITE locale (le soldat voit son voisin)
        px, py = self.body.apx, self.body.apy
        dx = targets[..., 0] - px; dy = targets[..., 1] - py
        dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
        th = torch.atan2(dx, dy)
        a_move = (torch.round(th / (math.pi / 4.0)) % 8).long()
        ndx, ndy, ndist = self._nearest_def(px, py)
        los = self.body._losc(self.body.hm, px, py, px + ndx, py + ndy, self.S)
        can_supp = (ndist < self.fire_range) & (los > 0.5)
        in_place = dist < 16.0
        a = torch.where(in_place, torch.where(can_supp, torch.full_like(a_move, 9), torch.full_like(a_move, 8)), a_move)
        return a

    def step(self, action):                            # action (N, K+1, 2) dans [-1,1] : [0..K-1]=elements, [K]=drone
        act_e = action[:, :self.K, :]
        act_d = action[:, self.K, :]
        # --- drone : vol délégué à vitesse finie vers la cible commandée ---
        dtx = act_d[:, 0].clamp(-1, 1) * self.R_drone
        dty = act_d[:, 1].clamp(-1, 1) * self.R_drone
        vx = dtx - self.drone_x; vy = dty - self.drone_y
        dd = torch.sqrt(vx * vx + vy * vy) + 1e-6
        sc = (self.drone_speed / dd).clamp(max=1.0)
        self.drone_x = self.drone_x + vx * sc; self.drone_y = self.drone_y + vy * sc
        # --- elements : seam positions -> waypoints bas-niveau ---
        tgt_e = act_e.clamp(-1, 1) * self.R_place
        targets = tgt_e[:, self.elem, :]
        for _ in range(self.t_low):
            a = self._lowlevel(targets)
            self.body.step(a, auto_reset=False)
        self.t_hi = self.t_hi + 1
        newly = self._update_belief()
        # --- recompense (identique au commandant + petit shaping reveal pour l'exploration) ---
        mind = self._min_obj_dist() / self.S
        dk = (self.body.ddmg >= self.body.dmg_dead).float().sum(1)
        alive = self.body._aalive().float().sum(1)
        secured = (self._min_obj_dist() < self.secure_r)
        wiped = alive < 0.5
        prog = (self._bestmin - mind).clamp(min=0)
        self._bestmin = torch.minimum(self._bestmin, mind)
        timeout_nosec = (self.t_hi >= self.maxT) & (~secured) & (~wiped)
        rew = (1.2 * prog
               + 0.4 * (dk - self._prevdk)
               - 0.3 * (self._prevalive - alive)
               - 0.02
               + 12.0 * secured.float()
               - 2.0 * timeout_nosec.float()
               + self.reveal_bonus * newly)           # exploration : voir du nouveau paie un peu
        done = secured | wiped | (self.t_hi >= self.maxT)
        info = {"secured": secured, "wiped": wiped, "neut": ~self.body._dalive().any(1),
                "alive": alive, "dk": dk, "known": (self.bel_known & self.body._dalive()).float().sum(1)}
        self._prevmin = mind; self._prevdk = dk; self._prevalive = alive
        return self._obs(), rew, done, info

    def reset_done(self, done):
        idx = done.nonzero(as_tuple=True)[0]
        if len(idx) == 0: return
        self.body._reset(idx); self.t_hi[idx] = 0
        self.bel_known[idx] = False; self.bel_age[idx] = self.forget_T + 10.0
        self.bel_x[idx] = 0.0; self.bel_y[idx] = 0.0
        self._drone_init(idx)
        self._update_belief()
        nm = (self._min_obj_dist() / self.S)[idx]
        self._prevmin[idx] = nm; self._bestmin[idx] = nm
        self._prevdk[idx] = (self.body.ddmg >= self.body.dmg_dead).float().sum(1)[idx]
        self._prevalive[idx] = self.body._aalive().float().sum(1)[idx]


if __name__ == "__main__":
    DEV = "cuda:0"
    def run(policy_fn, label, drone_r=70.0, N=1024, steps=16, seed=1):
        e = CommanderDroneEnv(N, A=8, K=2, D=8, device=DEV, seed=seed, drone_r=drone_r)
        obs = e.reset(); sec = neu = surv = nep = kn = 0.0
        for _ in range(steps):
            act = policy_fn(e, obs)
            obs, rew, done, info = e.step(act)
            dm = done
            if dm.any():
                sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / 8)[dm].sum().item(); kn += (info["known"] / 8)[dm].sum().item()
                nep += int(dm.sum()); e.reset_done(dm)
        print("  %-30s | securise %3.0f%% | neutralise %3.0f%% | survie %3.0f%% | connu %3.0f%% (%d ep)"
              % (label, 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1), 100 * kn / max(nep, 1), nep))

    print("=== CommanderDroneEnv : validation (avant entrainement) ===")
    def rnd(e, o): return torch.rand(e.N, e.K + 1, 2, device=DEV) * 2 - 1
    run(rnd, "ALEATOIRE (drone actif)", drone_r=70.0)
    run(rnd, "ALEATOIRE (drone AVEUGLE r=0)", drone_r=0.0)
    def hc(e, o):                                       # base de feu sud, assaut objectif, DRONE droit devant (nord)
        a = torch.zeros(e.N, e.K + 1, 2, device=DEV)
        a[:, 0, 0] = 0.0;  a[:, 0, 1] = -0.45
        a[:, 1, 0] = 0.15; a[:, 1, 1] = 0.0
        a[:, e.K, 0] = 0.0; a[:, e.K, 1] = 0.7         # drone : survol vers l'objectif/l'ennemi
        return a
    run(hc, "CODE-MAIN + drone en avant", drone_r=70.0)
    run(hc, "CODE-MAIN sans drone (r=0)", drone_r=0.0)
