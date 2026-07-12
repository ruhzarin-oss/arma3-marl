#!/usr/bin/env python3
"""reflex_fight_env_adv.py — VARIANTE de reflex_fight_env : AJOUTE un OBJECTIF + une recompense d'AVANCE.
But : corriger le GEL. Le soldat doit maintenant ATTEINDRE un objectif (defendu par K tireurs) EN AVANCANT sous le feu,
tout en ripostant/se couvrant. Recompense = neutraliser + survivre + PROGRESSER vers l'objectif + l'atteindre.
Original reflex_fight_env INTACT. Obs += 2 (direction de l'objectif, sinon le soldat ne sait pas ou avancer)."""
import math
import torch


class ReflexFightEnvAdv:
    def __init__(self, num_envs, device="cuda:0", K=3, Mobs=8, max_steps=50,
                 arena=100.0, move=7.0, p_base=0.28, q_base=0.45, maxr=85.0, orad=5.0,
                 blind=False, seed=0, adv=0.18, reach=10.0, reach_r=8.0, clock=0.006):
        self.N = num_envs; self.dev = device; self.K = K; self.Mobs = Mobs; self.max_steps = max_steps
        self.arena = arena; self.move = move; self.p_base = p_base; self.q_base = q_base
        self.maxr = maxr; self.orad = orad; self.blind = blind; self.D = 8
        self.adv = adv; self.reach = reach; self.reach_r = reach_r; self.clock = clock  # avance, atteinte, rayon, malus horloge
        self.span = 1.0                                                   # CURRICULUM distance : 0.45 (killzone courte) -> 1.0 (pleine)
        ang = torch.arange(self.D, device=device) * (2 * math.pi / self.D)
        self.dir_x = torch.cos(ang); self.dir_y = torch.sin(ang)
        self.obs_dim = self.D + 1 + self.D + 2 + 1 + 1 + 2                # R1(20) + tireurs restants(1) + DIR OBJECTIF(2)
        g = torch.Generator(device=device); g.manual_seed(seed); self.g = g
        self.sx = torch.zeros(self.N, device=device); self.sy = torch.zeros(self.N, device=device)
        self.gx = torch.zeros(self.N, device=device); self.gy = torch.zeros(self.N, device=device)
        self.prev_dobj = torch.zeros(self.N, device=device)
        self.alive = torch.ones(self.N, device=device); self.prone = torch.zeros(self.N, device=device)
        self.kx = torch.zeros(self.N, self.K, device=device); self.ky = torch.zeros(self.N, self.K, device=device)
        self.ka = torch.ones(self.N, self.K, device=device)
        self.ox = torch.zeros(self.N, self.Mobs, device=device); self.oy = torch.zeros(self.N, self.Mobs, device=device)
        self.t = torch.zeros(self.N, dtype=torch.long, device=device)
        self.reset(torch.arange(self.N, device=device))

    def reset(self, idx):
        n = idx.numel(); dev = self.dev; c = self.arena / 2
        self.alive[idx] = 1.0; self.prone[idx] = 0.0; self.t[idx] = 0; self.ka[idx] = 1.0
        # AXE aleatoire : soldat a un bout, objectif a l'AUTRE bout, tireurs dans la KILLZONE du milieu
        theta = torch.rand(n, generator=self.g, device=dev) * 2 * math.pi
        ux = torch.cos(theta); uy = torch.sin(theta); half = self.arena * 0.38 * self.span
        self.sx[idx] = c - half * ux; self.sy[idx] = c - half * uy         # depart
        self.gx[idx] = c + half * ux; self.gy[idx] = c + half * uy         # objectif (clair, a l'autre bout)
        # TIREURS : bande du milieu (entre le soldat et l'objectif), etales lateralement
        along = (torch.rand(n, self.K, generator=self.g, device=dev) - 0.5) * (half * 0.8)
        perp = (torch.rand(n, self.K, generator=self.g, device=dev) - 0.5) * (self.arena * 0.45)
        self.kx[idx] = c + along * ux[:, None] - perp * uy[:, None]
        self.ky[idx] = c + along * uy[:, None] + perp * ux[:, None]
        # OBSTACLES (couvert) disperses
        self.ox[idx] = self.arena * (0.12 + 0.76 * torch.rand(n, self.Mobs, generator=self.g, device=dev))
        self.oy[idx] = self.arena * (0.12 + 0.76 * torch.rand(n, self.Mobs, generator=self.g, device=dev))
        self.prev_dobj[idx] = torch.sqrt((self.sx[idx] - self.gx[idx]) ** 2 + (self.sy[idx] - self.gy[idx]) ** 2)

    def _los_clear(self, ax, ay, bx, by):
        ax = ax[:, :, None]; ay = ay[:, :, None]; bx = bx[:, :, None]; by = by[:, :, None]
        cx = self.ox[:, None, :]; cy = self.oy[:, None, :]
        ex = bx - ax; ey = by - ay; L2 = (ex * ex + ey * ey).clamp(min=1e-6)
        tt = (((cx - ax) * ex + (cy - ay) * ey) / L2).clamp(0, 1)
        px = ax + tt * ex; py = ay + tt * ey
        dist = torch.sqrt((cx - px) ** 2 + (cy - py) ** 2)
        return ~((dist < self.orad).any(-1))

    def _perception(self):
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float() * self.ka
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        threat = los * torch.clamp(1 - dist / self.maxr, 0.05, 1.0)
        bdx = self.kx - self.sx[:, None]; bdy = self.ky - self.sy[:, None]
        bn = torch.sqrt(bdx * bdx + bdy * bdy).clamp(min=1.0); bdx = bdx / bn; bdy = bdy / bn
        cosang = bdx[:, :, None] * self.dir_x[None, None, :] + bdy[:, :, None] * self.dir_y[None, None, :]
        sect = (cosang > math.cos(math.pi / self.D)).float()
        fire_dir = (sect * threat[:, :, None]).max(1).values
        exposed = los.mean(1, keepdim=True)
        odx = self.ox - self.sx[:, None]; ody = self.oy - self.sy[:, None]
        od = torch.sqrt(odx * odx + ody * ody).clamp(min=1.0); ndx = odx / od; ndy = ody / od
        ocos = ndx[:, :, None] * self.dir_x[None, None, :] + ndy[:, :, None] * self.dir_y[None, None, :]
        osect = (ocos > math.cos(math.pi / self.D)).float()
        close = torch.clamp(1 - od / self.arena, 0, 1)[:, :, None]
        cover_dir = (osect * close).max(1).values
        nearest = od.argmin(1)
        cvx = torch.gather(ndx, 1, nearest[:, None])[:, 0]; cvy = torch.gather(ndy, 1, nearest[:, None])[:, 0]
        left = self.ka.mean(1, keepdim=True)
        # DIRECTION DE L'OBJECTIF (normalisee) : le soldat sait ou avancer
        gdx = self.gx - self.sx; gdy = self.gy - self.sy
        gn = torch.sqrt(gdx * gdx + gdy * gdy).clamp(min=1.0); gdx = gdx / gn; gdy = gdy / gn
        obs = torch.cat([fire_dir, exposed, cover_dir, torch.stack([cvx, cvy], 1), self.prone[:, None], left,
                         torch.stack([gdx, gdy], 1)], 1)
        if self.blind:
            obs = obs.clone(); obs[:, :2 * self.D + 1 + 2] = 0.0                                # aveugle au feu + couvert (garde l'objectif)
        return obs

    def _obs(self):
        return self._perception()

    def step(self, move_act, stance_act, fire_act):
        a = self.alive; mv = move_act.long().clamp(0, self.D); st = stance_act.long().clamp(0, 1)
        self.prone = st.float()
        firing_now = (fire_act.long().clamp(0, self.D) > 0).float()
        moving = (mv > 0).float() * (1 - firing_now); di = (mv - 1).clamp(0, self.D - 1)
        spd = self.move * (0.5 + 0.5 * (1 - self.prone))
        self.sx = (self.sx + self.dir_x[di] * spd * moving * a).clamp(0, self.arena)
        self.sy = (self.sy + self.dir_y[di] * spd * moving * a).clamp(0, self.arena)
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float() * self.ka
        # 1) RIPOSTE VISEE (R2)
        bdx = self.kx - self.sx[:, None]; bdy = self.ky - self.sy[:, None]
        bn = torch.sqrt(bdx * bdx + bdy * bdy).clamp(min=1.0); bdx = bdx / bn; bdy = bdy / bn
        ksect = (bdx[:, :, None] * self.dir_x[None, None, :] + bdy[:, :, None] * self.dir_y[None, None, :]).argmax(2)
        fsec = fire_act.long().clamp(0, self.D) - 1
        firing = (fire_act.long() > 0) & (a > 0)
        hittable = (self.ka > 0) & (los > 0) & (ksect == fsec[:, None]) & firing[:, None]
        far = dist + (~hittable).float() * 1e6
        tgt = far.argmin(1); has = hittable.gather(1, tgt[:, None])[:, 0]
        qhit = self.q_base * torch.clamp(1 - dist.gather(1, tgt[:, None])[:, 0] / self.maxr, 0.1, 1.0) * has.float()
        killshot = (torch.rand(self.N, generator=self.g, device=self.dev) < qhit)
        ksrc = torch.zeros(self.N, self.K, device=self.dev); ksrc.scatter_(1, tgt[:, None], killshot.float()[:, None])
        newly = (ksrc > 0) & (self.ka > 0); self.ka = self.ka * (~newly).float()
        nkilled = newly.float().sum(1)
        # 2) FEU ENNEMI
        los2 = los * self.ka
        hitp = self.p_base * torch.clamp(1 - dist / self.maxr, 0.05, 1.0) * los2
        hitp = hitp * (0.35 + 0.65 * (1 - self.prone))[:, None] * (1 + 0.35 * firing_now)[:, None]
        surv = torch.prod(1 - hitp, dim=1)
        killed = (torch.rand(self.N, generator=self.g, device=self.dev) > surv) & (a > 0)
        self.alive = self.alive * (~killed).float()
        self.t = self.t + 1
        # 3) AVANCE VERS L'OBJECTIF (le geste manquant)
        dobj = torch.sqrt((self.sx - self.gx) ** 2 + (self.sy - self.gy) ** 2)
        progress = (self.prev_dobj - dobj) * a                            # avance nette ce pas (0 si mort)
        self.prev_dobj = dobj
        reached = (dobj < self.reach_r) & (a > 0)
        cleared = (self.ka.sum(1) <= 0)
        rew = (2.5 * nkilled + 0.03 * self.alive - 1.5 * killed.float() + 1.5 * (cleared & (a > 0)).float()
               + self.adv * progress + self.reach * reached.float()
               - self.clock * (a > 0).float() * (~reached).float())     # avancer PRUDEMMENT : survie + suppression valorisees, horloge douce
        done = (self.t >= self.max_steps) | (self.alive <= 0) | reached
        final_alive = self.alive.clone(); ncleared = (self.K - self.ka.sum(1)); final_reached = reached.clone(); final_dobj = dobj.clone()
        di_ = torch.where(done)[0]
        if di_.numel() > 0: self.reset(di_)
        obs = self._obs()
        return obs, rew, done.float(), {"alive": final_alive, "killed": ncleared, "reached": final_reached, "dobj": final_dobj}
