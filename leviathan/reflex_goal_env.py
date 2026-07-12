#!/usr/bin/env python3
"""reflex_goal_env.py — BRIQUE 3 : R5 LOCOMOTION-VERS-BUT. Le soldat doit ATTEINDRE un objectif en traversant un champ
de tir (K tireurs en bande), en EXPLOITANT le couvert/defile — pas juste survivre (R1) mais PROGRESSER vivant.
C'est le chainon entre le cerveau abstrait (« va a l'objectif ») et le corps. Perception R1 + direction/distance du but.
A/B : voyant (sens du feu + couvert + but) vs aveugle (ne voit que le but) -> traverse-t-il en se servant du terrain ?"""
import math
import torch


class ReflexGoalEnv:
    def __init__(self, num_envs, device="cuda:0", K=3, Mobs=13, max_steps=45,
                 arena=120.0, move=7.0, p_base=0.26, maxr=95.0, orad=5.0, reach=9.0, blind=False, routed=False, seed=0):
        self.routed = routed                                          # routed=True : un ROUTEUR (= le chef) donne le prochain couvert
        self.N = num_envs; self.dev = device; self.K = K; self.Mobs = Mobs; self.max_steps = max_steps
        self.arena = arena; self.move = move; self.p_base = p_base; self.maxr = maxr; self.orad = orad
        self.reach = reach; self.blind = blind; self.D = 8
        ang = torch.arange(self.D, device=device) * (2 * math.pi / self.D)
        self.dir_x = torch.cos(ang); self.dir_y = torch.sin(ang)
        self.obs_dim = self.D + 1 + self.D + 2 + 1 + 2 + 1            # R1(20) + vecteur but(2) + distance but(1)
        g = torch.Generator(device=device); g.manual_seed(seed); self.g = g
        self.sx = torch.zeros(self.N, device=device); self.sy = torch.zeros(self.N, device=device)
        self.gx = torch.zeros(self.N, device=device); self.gy = torch.zeros(self.N, device=device)
        self.alive = torch.ones(self.N, device=device); self.prone = torch.zeros(self.N, device=device)
        self.reached = torch.zeros(self.N, device=device); self.pd = torch.zeros(self.N, device=device)
        self.kx = torch.zeros(self.N, self.K, device=device); self.ky = torch.zeros(self.N, self.K, device=device)
        self.ox = torch.zeros(self.N, self.Mobs, device=device); self.oy = torch.zeros(self.N, self.Mobs, device=device)
        self.t = torch.zeros(self.N, dtype=torch.long, device=device)
        self.reset(torch.arange(self.N, device=device))

    def reset(self, idx):
        n = idx.numel(); dev = self.dev; A = self.arena
        self.sx[idx] = A * (0.2 + 0.6 * torch.rand(n, generator=self.g, device=dev)); self.sy[idx] = A * 0.08   # depart en bas
        self.gx[idx] = A * (0.2 + 0.6 * torch.rand(n, generator=self.g, device=dev)); self.gy[idx] = A * 0.92   # but en haut
        self.alive[idx] = 1.0; self.prone[idx] = 0.0; self.reached[idx] = 0.0; self.t[idx] = 0
        self.pd[idx] = torch.sqrt((self.sx[idx] - self.gx[idx]) ** 2 + (self.sy[idx] - self.gy[idx]) ** 2)
        # tireurs en BANDE au milieu (gardent l'approche) + obstacles disperses (couvert pour router)
        self.kx[idx] = A * (0.1 + 0.8 * torch.rand(n, self.K, generator=self.g, device=dev))
        self.ky[idx] = A * (0.40 + 0.20 * torch.rand(n, self.K, generator=self.g, device=dev))
        self.ox[idx] = A * (0.1 + 0.8 * torch.rand(n, self.Mobs, generator=self.g, device=dev))
        self.oy[idx] = A * (0.12 + 0.76 * torch.rand(n, self.Mobs, generator=self.g, device=dev))

    def _los_clear(self, ax, ay, bx, by):
        ax = ax[:, :, None]; ay = ay[:, :, None]; bx = bx[:, :, None]; by = by[:, :, None]
        cx = self.ox[:, None, :]; cy = self.oy[:, None, :]
        ex = bx - ax; ey = by - ay; L2 = (ex * ex + ey * ey).clamp(min=1e-6)
        tt = (((cx - ax) * ex + (cy - ay) * ey) / L2).clamp(0, 1)
        px = ax + tt * ex; py = ay + tt * ey
        dist = torch.sqrt((cx - px) ** 2 + (cy - py) ** 2)
        return ~((dist < self.orad).any(-1))

    def _waypoint(self):
        # ROUTEUR (= le commandant) : prochain waypoint = le couvert le plus AVANCE vers le but et atteignable.
        # Le soldat n'a plus qu'a bondir couvert-a-couvert ; le routeur fait la planification, le reflexe l'execution.
        sg = torch.sqrt((self.sx - self.gx) ** 2 + (self.sy - self.gy) ** 2)
        og = torch.sqrt((self.ox - self.gx[:, None]) ** 2 + (self.oy - self.gy[:, None]) ** 2)
        so = torch.sqrt((self.ox - self.sx[:, None]) ** 2 + (self.oy - self.sy[:, None]) ** 2)
        ok = (og < sg[:, None] - 4.0) & (so < 52.0)                   # le couvert avance vers le but ET est atteignable
        prog = (sg[:, None] - og).clamp(min=0)
        score = torch.where(ok, prog, torch.full_like(prog, -1e9)); best = score.argmax(1)
        wx = torch.gather(self.ox, 1, best[:, None])[:, 0]; wy = torch.gather(self.oy, 1, best[:, None])[:, 0]
        has = ok.any(1)
        return torch.where(has, wx, self.gx), torch.where(has, wy, self.gy)   # sinon : droit vers le but

    def _perception(self):
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float()
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
        # direction de la CIBLE (le waypoint du routeur si routed, sinon le but lointain) + distance du but reel
        tx, ty = self._waypoint() if self.routed else (self.gx, self.gy)
        gdx = tx - self.sx; gdy = ty - self.sy; gd = torch.sqrt(gdx * gdx + gdy * gdy).clamp(min=1.0)
        gvec = torch.stack([gdx / gd, gdy / gd], 1)
        fardist = torch.sqrt((self.gx - self.sx) ** 2 + (self.gy - self.sy) ** 2)
        gdn = (fardist / (self.arena * 1.4)).clamp(0, 1)[:, None]
        spatial = torch.cat([fire_dir, exposed, cover_dir, torch.stack([cvx, cvy], 1), self.prone[:, None]], 1)
        if self.blind:
            spatial = torch.zeros_like(spatial); spatial[:, 2 * self.D + 1 + 2] = self.prone    # ne garde que sa posture
        return torch.cat([spatial, gvec, gdn], 1)

    def _obs(self):
        return self._perception()

    def step(self, move_act, stance_act):
        a = self.alive; mv = move_act.long().clamp(0, self.D); st = stance_act.long().clamp(0, 1)
        self.prone = st.float()
        moving = (mv > 0).float(); di = (mv - 1).clamp(0, self.D - 1)
        spd = self.move * (0.5 + 0.5 * (1 - self.prone))
        self.sx = (self.sx + self.dir_x[di] * spd * moving * a).clamp(0, self.arena)
        self.sy = (self.sy + self.dir_y[di] * spd * moving * a).clamp(0, self.arena)
        # feu ennemi
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float()
        hitp = self.p_base * torch.clamp(1 - dist / self.maxr, 0.05, 1.0) * los
        hitp = hitp * (0.35 + 0.65 * (1 - self.prone))[:, None]
        surv = torch.prod(1 - hitp, dim=1)
        killed = (torch.rand(self.N, generator=self.g, device=self.dev) > surv) & (a > 0)
        self.alive = self.alive * (~killed).float()
        # progression vers le but
        gd = torch.sqrt((self.sx - self.gx) ** 2 + (self.sy - self.gy) ** 2)
        progress = (self.pd - gd) * a; self.pd = gd
        reach_now = (gd < self.reach) & (a > 0) & (self.reached < 1)
        self.reached = torch.clamp(self.reached + reach_now.float(), 0, 1)
        self.t = self.t + 1
        not_reached = ((self.alive > 0) & (self.reached < 1)).float()
        rew = 0.25 * progress + 12.0 * reach_now.float() - 3.0 * killed.float() - 0.06 * not_reached   # progrès dominant + urgence (se cacher coûte)
        done = (self.t >= self.max_steps) | (self.alive <= 0) | (self.reached > 0)
        reached_alive = ((self.reached > 0) & (self.alive > 0)).float()      # atteint le but VIVANT (la metrique)
        surv_now = (self.alive > 0).float()                                  # survie a l'instant du done (avant reset)
        di_ = torch.where(done)[0]
        if di_.numel() > 0: self.reset(di_)
        obs = self._obs()
        return obs, rew, done.float(), {"reached": reached_alive, "alive": surv_now}
