#!/usr/bin/env python3
"""reflex_fight_env.py — BRIQUE 2 de la boucle : R2 tir reactif + R3 micro-couvert (peek-and-shoot).
Le soldat ne survit plus seulement : il RIPOSTE et doit NEUTRALISER les K tireurs depuis le couvert.
Tension = pour tirer il faut la LOS -> donc s'exposer -> donc le rythme couvert/feu/couvert (R3).
Meme perception que R1 (le sens du feu entrant sert AUSSI a viser : these de Younes « la perception s'ingenie,
l'usage s'apprend »). Tir auto quand LOS sur un tireur vivant. Vectorise GPU. A/B voyant vs aveugle."""
import math
import torch


class ReflexFightEnv:
    def __init__(self, num_envs, device="cuda:0", K=3, Mobs=8, max_steps=50,
                 arena=100.0, move=7.0, p_base=0.28, q_base=0.45, maxr=85.0, orad=5.0, blind=False, seed=0):
        self.N = num_envs; self.dev = device; self.K = K; self.Mobs = Mobs; self.max_steps = max_steps
        self.arena = arena; self.move = move; self.p_base = p_base; self.q_base = q_base
        self.maxr = maxr; self.orad = orad; self.blind = blind; self.D = 8
        ang = torch.arange(self.D, device=device) * (2 * math.pi / self.D)
        self.dir_x = torch.cos(ang); self.dir_y = torch.sin(ang)
        self.obs_dim = self.D + 1 + self.D + 2 + 1 + 1                # R1(20) + fraction de tireurs restants(1)
        g = torch.Generator(device=device); g.manual_seed(seed); self.g = g
        self.sx = torch.zeros(self.N, device=device); self.sy = torch.zeros(self.N, device=device)
        self.alive = torch.ones(self.N, device=device); self.prone = torch.zeros(self.N, device=device)
        self.kx = torch.zeros(self.N, self.K, device=device); self.ky = torch.zeros(self.N, self.K, device=device)
        self.ka = torch.ones(self.N, self.K, device=device)          # tireur vivant
        self.ox = torch.zeros(self.N, self.Mobs, device=device); self.oy = torch.zeros(self.N, self.Mobs, device=device)
        self.t = torch.zeros(self.N, dtype=torch.long, device=device)
        self.reset(torch.arange(self.N, device=device))

    def reset(self, idx):
        n = idx.numel(); dev = self.dev; c = self.arena / 2
        self.sx[idx] = c; self.sy[idx] = c; self.alive[idx] = 1.0; self.prone[idx] = 0.0; self.t[idx] = 0
        self.ka[idx] = 1.0
        a = torch.rand(n, self.K, generator=self.g, device=dev) * 2 * math.pi
        r = self.arena * 0.42 + torch.rand(n, self.K, generator=self.g, device=dev) * self.arena * 0.06
        self.kx[idx] = c + r * torch.cos(a); self.ky[idx] = c + r * torch.sin(a)
        self.ox[idx] = self.arena * (0.18 + 0.64 * torch.rand(n, self.Mobs, generator=self.g, device=dev))
        self.oy[idx] = self.arena * (0.18 + 0.64 * torch.rand(n, self.Mobs, generator=self.g, device=dev))

    def _los_clear(self, ax, ay, bx, by):
        ax = ax[:, :, None]; ay = ay[:, :, None]; bx = bx[:, :, None]; by = by[:, :, None]
        cx = self.ox[:, None, :]; cy = self.oy[:, None, :]
        ex = bx - ax; ey = by - ay; L2 = (ex * ex + ey * ey).clamp(min=1e-6)
        tt = (((cx - ax) * ex + (cy - ay) * ey) / L2).clamp(0, 1)
        px = ax + tt * ex; py = ay + tt * ey
        dist = torch.sqrt((cx - px) ** 2 + (cy - py) ** 2)
        return ~((dist < self.orad).any(-1))

    def _perception(self):
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float() * self.ka   # tireur VIVANT qui me voit
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        threat = los * torch.clamp(1 - dist / self.maxr, 0.05, 1.0)
        bdx = self.kx - self.sx[:, None]; bdy = self.ky - self.sy[:, None]
        bn = torch.sqrt(bdx * bdx + bdy * bdy).clamp(min=1.0); bdx = bdx / bn; bdy = bdy / bn
        cosang = bdx[:, :, None] * self.dir_x[None, None, :] + bdy[:, :, None] * self.dir_y[None, None, :]
        sect = (cosang > math.cos(math.pi / self.D)).float()
        fire_dir = (sect * threat[:, :, None]).max(1).values                                # sert au feu reçu ET a viser
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
        obs = torch.cat([fire_dir, exposed, cover_dir, torch.stack([cvx, cvy], 1), self.prone[:, None], left], 1)
        if self.blind:
            obs = obs.clone(); obs[:, :2 * self.D + 1 + 2] = 0.0                              # aveugle au feu + couvert
        return obs

    def _obs(self):
        return self._perception()

    def step(self, move_act, stance_act, fire_act):
        a = self.alive; mv = move_act.long().clamp(0, self.D); st = stance_act.long().clamp(0, 1)
        self.prone = st.float()
        firing_now = (fire_act.long().clamp(0, self.D) > 0).float()         # MANIEMENT D'ARME : tirer = s'arreter (on ne sprinte pas en visant)
        moving = (mv > 0).float() * (1 - firing_now); di = (mv - 1).clamp(0, self.D - 1)
        spd = self.move * (0.5 + 0.5 * (1 - self.prone))
        self.sx = (self.sx + self.dir_x[di] * spd * moving * a).clamp(0, self.arena)
        self.sy = (self.sy + self.dir_y[di] * spd * moving * a).clamp(0, self.arena)
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float() * self.ka
        # 1) RIPOSTE VISEE (R2) : le soldat TIRE dans un secteur choisi -> ne touche qu'un tireur vivant+LOS dans CE secteur.
        #    => viser exige de savoir d'ou ca tire (le sens du feu) ; tirer a l'aveugle = secteur au hasard = rate.
        bdx = self.kx - self.sx[:, None]; bdy = self.ky - self.sy[:, None]
        bn = torch.sqrt(bdx * bdx + bdy * bdy).clamp(min=1.0); bdx = bdx / bn; bdy = bdy / bn
        ksect = (bdx[:, :, None] * self.dir_x[None, None, :] + bdy[:, :, None] * self.dir_y[None, None, :]).argmax(2)  # (N,K)
        fsec = fire_act.long().clamp(0, self.D) - 1                                            # -1 = ne tire pas ; 0..D-1 = secteur
        firing = (fire_act.long() > 0) & (a > 0)
        hittable = (self.ka > 0) & (los > 0) & (ksect == fsec[:, None]) & firing[:, None]      # tireur dans le secteur vise + LOS
        far = dist + (~hittable).float() * 1e6
        tgt = far.argmin(1); has = hittable.gather(1, tgt[:, None])[:, 0]
        qhit = self.q_base * torch.clamp(1 - dist.gather(1, tgt[:, None])[:, 0] / self.maxr, 0.1, 1.0) * has.float()
        killshot = (torch.rand(self.N, generator=self.g, device=self.dev) < qhit)
        ksrc = torch.zeros(self.N, self.K, device=self.dev); ksrc.scatter_(1, tgt[:, None], killshot.float()[:, None])
        newly = (ksrc > 0) & (self.ka > 0); self.ka = self.ka * (~newly).float()
        nkilled = newly.float().sum(1)
        # 2) FEU ENNEMI : les tireurs VIVANTS me touchent si LOS (recalcule apres morts)
        los2 = los * self.ka
        hitp = self.p_base * torch.clamp(1 - dist / self.maxr, 0.05, 1.0) * los2
        hitp = hitp * (0.35 + 0.65 * (1 - self.prone))[:, None] * (1 + 0.35 * firing_now)[:, None]   # tirer (statique) = plus expose
        surv = torch.prod(1 - hitp, dim=1)
        killed = (torch.rand(self.N, generator=self.g, device=self.dev) > surv) & (a > 0)
        self.alive = self.alive * (~killed).float()
        self.t = self.t + 1
        cleared = (self.ka.sum(1) <= 0)
        rew = 2.0 * nkilled + 0.03 * self.alive - 1.0 * killed.float() + 1.5 * (cleared & (a > 0)).float()
        done = (self.t >= self.max_steps) | (self.alive <= 0) | cleared
        final_alive = self.alive.clone(); ncleared = (self.K - self.ka.sum(1))
        di_ = torch.where(done)[0]
        if di_.numel() > 0: self.reset(di_)
        obs = self._obs()
        return obs, rew, done.float(), {"alive": final_alive, "killed": ncleared}
