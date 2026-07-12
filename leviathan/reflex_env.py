#!/usr/bin/env python3
"""reflex_env.py — BRIQUE 1 de la boucle complete (corps appris vs LAMBS) : R1 REACTION AU FEU + SENS DU FEU ENTRANT.
Un soldat SEUL sous le feu de K tireurs doit apprendre le reflexe : sentir d'ou ca tire + gagner le couvert / se mettre
a terre pour casser la LOS et survivre. Vectorise (N mondes paralleles, GPU). La perception = le « sens du feu entrant ».
Preuve attendue (a la +97 du couvert) : un soldat AVEC le sens du feu survit bien plus qu'un soldat AVEUGLE."""
import math
import torch


class ReflexEnv:
    def __init__(self, num_envs, device="cuda:0", K=4, Mobs=6, max_steps=40,
                 arena=100.0, move=6.0, p_base=0.38, maxr=85.0, orad=5.0, blind=False, seed=0):
        self.N = num_envs; self.dev = device; self.K = K; self.Mobs = Mobs; self.max_steps = max_steps
        self.arena = arena; self.move = move; self.p_base = p_base; self.maxr = maxr; self.orad = orad
        self.blind = blind                                            # ablation : obs du feu/couvert mise a zero
        self.D = 8                                                    # 8 secteurs de perception
        ang = torch.arange(self.D, device=device) * (2 * math.pi / self.D)
        self.dir_x = torch.cos(ang); self.dir_y = torch.sin(ang)     # directions de deplacement / secteurs
        self.obs_dim = self.D + 1 + self.D + 2 + 1                    # feu[8] + expose[1] + couvert[8] + vec_couvert[2] + prone[1]
        g = torch.Generator(device=device); g.manual_seed(seed); self.g = g
        self.sx = torch.zeros(self.N, device=device); self.sy = torch.zeros(self.N, device=device)
        self.alive = torch.ones(self.N, device=device); self.prone = torch.zeros(self.N, device=device)
        self.kx = torch.zeros(self.N, self.K, device=device); self.ky = torch.zeros(self.N, self.K, device=device)
        self.ox = torch.zeros(self.N, self.Mobs, device=device); self.oy = torch.zeros(self.N, self.Mobs, device=device)
        self.t = torch.zeros(self.N, dtype=torch.long, device=device)
        self.reset(torch.arange(self.N, device=device))

    def reset(self, idx):
        n = idx.numel(); dev = self.dev; c = self.arena / 2
        self.sx[idx] = c; self.sy[idx] = c; self.alive[idx] = 1.0; self.prone[idx] = 0.0; self.t[idx] = 0
        # tireurs sur un anneau autour du soldat (angles aleatoires) -> il DEMARRE expose
        a = torch.rand(n, self.K, generator=self.g, device=dev) * 2 * math.pi
        r = self.arena * 0.42 + torch.rand(n, self.K, generator=self.g, device=dev) * self.arena * 0.06
        self.kx[idx] = c + r * torch.cos(a); self.ky[idx] = c + r * torch.sin(a)
        # obstacles disperses (couvert atteignable) ; au moins quelques-uns proches du centre
        self.ox[idx] = self.arena * (0.18 + 0.64 * torch.rand(n, self.Mobs, generator=self.g, device=dev))
        self.oy[idx] = self.arena * (0.18 + 0.64 * torch.rand(n, self.Mobs, generator=self.g, device=dev))

    def _los_clear(self, ax, ay, bx, by):
        # LOS degagee de a (N,K) vers b (soldat, N,1) si aucun obstacle (N,Mobs) ne coupe le segment
        ax = ax[:, :, None]; ay = ay[:, :, None]; bx = bx[:, :, None]; by = by[:, :, None]   # (N,K,1)
        cx = self.ox[:, None, :]; cy = self.oy[:, None, :]                                    # (N,1,Mobs)
        ex = bx - ax; ey = by - ay; L2 = (ex * ex + ey * ey).clamp(min=1e-6)
        tt = (((cx - ax) * ex + (cy - ay) * ey) / L2).clamp(0, 1)
        px = ax + tt * ex; py = ay + tt * ey
        dist = torch.sqrt((cx - px) ** 2 + (cy - py) ** 2)                                    # (N,K,Mobs)
        blocked = (dist < self.orad).any(-1)                                                 # (N,K)
        return ~blocked

    def _perception(self):
        # vecteurs tireurs->soldat, LOS, distance
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky                      # (N,K) du tireur vers soi
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float()   # (N,K) ce tireur me voit-il
        threat = los * torch.clamp(1 - dist / self.maxr, 0.05, 1.0)                           # intensite du feu recu
        # SENS DU FEU ENTRANT : par secteur, max du feu venant de cette direction (le tireur est en -dx,-dy)
        bdx = self.kx - self.sx[:, None]; bdy = self.ky - self.sy[:, None]                     # vers le tireur
        bn = torch.sqrt(bdx * bdx + bdy * bdy).clamp(min=1.0); bdx = bdx / bn; bdy = bdy / bn
        cosang = bdx[:, :, None] * self.dir_x[None, None, :] + bdy[:, :, None] * self.dir_y[None, None, :]  # (N,K,D)
        sect = (cosang > math.cos(math.pi / self.D)).float()                                  # tireur dans ce secteur
        fire_dir = (sect * threat[:, :, None]).max(1).values                                  # (N,D)
        exposed = los.mean(1, keepdim=True)                                                   # fraction qui me voit
        # SENS DU COUVERT : par secteur, proximite de l'obstacle le plus proche dans cette direction
        odx = self.ox - self.sx[:, None]; ody = self.oy - self.sy[:, None]
        od = torch.sqrt(odx * odx + ody * ody).clamp(min=1.0); ndx = odx / od; ndy = ody / od
        ocos = ndx[:, :, None] * self.dir_x[None, None, :] + ndy[:, :, None] * self.dir_y[None, None, :]    # (N,Mobs,D)
        osect = (ocos > math.cos(math.pi / self.D)).float()
        close = torch.clamp(1 - od / self.arena, 0, 1)[:, :, None]
        cover_dir = (osect * close).max(1).values                                            # (N,D)
        # vecteur vers le couvert le plus proche
        nearest = od.argmin(1)
        cvx = torch.gather(ndx, 1, nearest[:, None])[:, 0]; cvy = torch.gather(ndy, 1, nearest[:, None])[:, 0]
        obs = torch.cat([fire_dir, exposed, cover_dir, torch.stack([cvx, cvy], 1), self.prone[:, None]], 1)
        if self.blind:
            obs = obs.clone(); obs[:, :self.D + 1] = 0.0; obs[:, self.D + 1:2 * self.D + 1 + 2] = 0.0       # aveugle au feu + couvert
        return obs

    def _obs(self):
        return self._perception()

    def step(self, move_act, stance_act):
        a = self.alive; mv = move_act.long().clamp(0, self.D); st = stance_act.long().clamp(0, 1)
        self.prone = st.float()
        # 1) deplacement (0 = rester ; 1..D = direction) ; prone = plus lent
        moving = (mv > 0).float()
        di = (mv - 1).clamp(0, self.D - 1)
        spd = self.move * (0.5 + 0.5 * (1 - self.prone))                                      # prone -> moitie vitesse
        self.sx = (self.sx + self.dir_x[di] * spd * moving * a).clamp(0, self.arena)
        self.sy = (self.sy + self.dir_y[di] * spd * moving * a).clamp(0, self.arena)
        # 2) FEU des tireurs : touche si LOS, module par distance, posture (prone protege), mouvement a decouvert expose
        dx = self.sx[:, None] - self.kx; dy = self.sy[:, None] - self.ky
        dist = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)
        los = self._los_clear(self.kx, self.ky, self.sx[:, None], self.sy[:, None]).float()
        hitp = self.p_base * torch.clamp(1 - dist / self.maxr, 0.05, 1.0) * los
        hitp = hitp * (0.35 + 0.65 * (1 - self.prone))[:, None]                               # prone -> ~1/3 du risque
        surv = torch.prod(1 - hitp, dim=1)                                                    # survie a la salve combinee
        killed = (torch.rand(self.N, generator=self.g, device=self.dev) > surv) & (a > 0)
        self.alive = self.alive * (~killed).float()
        self.t = self.t + 1
        rew = self.alive.clone()                                                             # +1 par pas survecu
        done = (self.t >= self.max_steps) | (self.alive <= 0)
        final_alive = self.alive.clone()                                                     # survie a l'instant du done (AVANT reset)
        di_ = torch.where(done)[0]
        if di_.numel() > 0: self.reset(di_)
        obs = self._obs()
        return obs, rew, done.float(), {"alive": final_alive}
