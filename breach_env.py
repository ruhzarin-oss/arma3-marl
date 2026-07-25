"""BreachEnv — brique BRECHE (forces speciales). L'agent doit NEUTRALISER SILENCIEUSEMENT un garde cible :
l'approcher par son ANGLE MORT (derriere, hors de son cone), a courte portee, SANS declencher l'alarme,
puis executer le takedown (action 9). Le garde neutralise => son cone disparait => un TROU s'ouvre dans l'anneau.
Reutilise AssaultTerrain (cones/detection comme StealthEnv) + cible designee (garde 0)."""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


class BreachEnv:
    def __init__(self, num_envs, A=1, D=3, device="cuda:0", seed=0, replica=True,
                 replica_path="/home/younes/arma3-marl/replica.npz", fov_deg=25.0, drange=70.0,
                 alarm=3.0, max_steps=120, td_range=10.0, td_arc_deg=75.0, target=0,
                 spawn_r=None, spawn_jit_deg=180.0):
        self.B = AssaultTerrain(num_envs=num_envs, A=A, D=D, device=device, seed=seed, move=6.0,
                                replica=replica, replica_path=replica_path, shell_obs=True, max_steps=10 ** 9)   # pas FIN : positionnement precis (zone takedown 10 m)
        self.N, self.A, self.D, self.dev, self.S = num_envs, A, D, device, self.B.scale
        self.fov = math.radians(fov_deg); self.drange = drange; self.secure_r = 20.0
        self.alarm, self.max_steps = alarm, max_steps; self.n_actions = self.B.n_actions
        self.T = min(target, D - 1); self.td_range = td_range; self.td_arc = math.radians(td_arc_deg)
        self.spawn_r = spawn_r; self.spawn_jit = math.radians(spawn_jit_deg)   # curriculum de SPAWN (None = defaut moteur)
        z = lambda: torch.zeros(num_envs, device=device)
        self.t, self.alert = z(), z()
        self.gface = torch.zeros(num_envs, D, device=device)
        self.prevdt = torch.zeros(num_envs, device=device)
        self._reset(torch.arange(num_envs, device=device))
        self.obs_dim = self._obs().shape[-1]

    def _reset(self, ids):
        if ids.numel() == 0: return
        self.B._reset(ids)
        self.gface[ids] = torch.atan2(self.B.dpy[ids], self.B.dpx[ids])     # gardes regardent VERS L'EXTERIEUR
        if self.spawn_r is not None:                                        # CURRICULUM DE SPAWN : poser l'agent dans le dos du garde cible
            tgx = self.B.dpx[ids, self.T]; tgy = self.B.dpy[ids, self.T]
            rear = self.gface[ids, self.T] + math.pi                        # direction "derriere" (vers le centre)
            jit = (torch.rand(ids.numel(), device=self.dev, generator=self.B.g) * 2 - 1) * self.spawn_jit
            ang = rear + jit
            self.B.apx[ids, 0] = tgx + self.spawn_r * torch.cos(ang)
            self.B.apy[ids, 0] = tgy + self.spawn_r * torch.sin(ang)
        self.alert[ids] = 0.0; self.t[ids] = 0.0
        self.prevdt[ids] = self._tgt(ids)[1]

    def reset(self):
        self._reset(torch.arange(self.N, device=self.dev)); return self._obs()

    def _tgt(self, ids=None):                                              # cible : dir(2), dist, off(rad), behind[0..1], alive
        ax = self.B.apx[:, 0]; ay = self.B.apy[:, 0]
        if ids is not None: ax, ay = self.B.apx[ids, 0], self.B.apy[ids, 0]
        gx = self.B.dpx[:, self.T] if ids is None else self.B.dpx[ids, self.T]
        gy = self.B.dpy[:, self.T] if ids is None else self.B.dpy[ids, self.T]
        gf = self.gface[:, self.T] if ids is None else self.gface[ids, self.T]
        dx = gx - ax; dy = gy - ay; dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
        ang = torch.atan2(ay - gy, ax - gx)                                # garde -> agent
        off = (ang - gf).abs(); off = torch.minimum(off, 2 * math.pi - off)
        behind = ((off - self.fov) / (math.pi - self.fov)).clamp(0, 1)     # 0 dans/pres du cone, 1 plein dos
        alive = (self.B.ddmg[:, self.T] < self.B.dmg_dead).float() if ids is None else (self.B.ddmg[ids, self.T] < self.B.dmg_dead).float()
        return torch.stack([dx, dy], -1), dist, off, behind, alive

    def _detect(self):
        ax, ay, N, A = self.B.apx, self.B.apy, self.N, self.A
        det = torch.zeros(N, A, dtype=torch.bool, device=self.dev); expo = torch.zeros(N, A, device=self.dev)
        ng_d2 = torch.full((N, A), 1e18, device=self.dev); ngx = torch.zeros(N, A, device=self.dev); ngy = torch.zeros(N, A, device=self.dev); ng_e = torch.zeros(N, A, device=self.dev)
        for di in range(self.D):
            gx = self.B.dpx[:, di:di + 1]; gy = self.B.dpy[:, di:di + 1]; gf = self.gface[:, di:di + 1]
            dx = ax - gx; dy = ay - gy; dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
            off = (torch.atan2(dy, dx) - gf).abs(); off = torch.minimum(off, 2 * math.pi - off)
            los = self.B._losc(self.B.hm, gx.expand(N, A), gy.expand(N, A), ax, ay, self.S)
            inr = (dist < self.drange) & self.B._dalive()[:, di:di + 1]
            det = det | ((off < self.fov) & inr & (los > 0.5))
            e = (1 - off / self.fov).clamp(min=0) * inr.float() * los; expo = torch.maximum(expo, e)
            closer = (dist * dist) < ng_d2
            ng_d2 = torch.where(closer, dist * dist, ng_d2); ngx = torch.where(closer, gx - ax, ngx); ngy = torch.where(closer, gy - ay, ngy); ng_e = torch.where(closer, e, ng_e)
        return det, expo, ngx, ngy, ng_e

    def _obs(self):
        S, ax, ay = self.S, self.B.apx, self.B.apy
        shell = self.B._cover_shell()
        d = torch.sqrt(ax ** 2 + ay ** 2) + 1e-6
        toobj = torch.stack([-ax / d, -ay / d, (d / S).clamp(max=2.0)], dim=2)
        det, expo, ngx, ngy, nge = self._detect()
        ngd = torch.sqrt(ngx ** 2 + ngy ** 2) + 1e-6
        gobs = torch.stack([ngx / ngd, ngy / ngd, (ngd / S).clamp(max=2.0), nge], dim=2)
        extra = torch.stack([expo, det.float(), self.B.admg], dim=2)
        tdir, tdist, toff, tbehind, talive = self._tgt()
        tb = torch.stack([tdir[:, 0] / tdist, tdir[:, 1] / tdist, (tdist / S).clamp(max=2.0), tbehind, talive], -1).unsqueeze(1)
        return torch.cat([shell, toobj, gobs, extra, tb], dim=2)

    def step(self, acts):
        move = acts.clone(); move[acts == 9] = 8                           # action 9 inutile -> hold (pas de suppress bruyant)
        self.B.step(move, auto_reset=False)
        _, tdist, toff, tbehind, talive = self._tgt()
        det, _, _, _, _ = self._detect()
        ds = det.float().squeeze(1) if self.A == 1 else det.float().mean(1)
        self.alert = self.alert + ds; undet = 1.0 - ds
        ready = (tdist < self.td_range) & (toff > self.td_arc) & (talive > 0.5)
        killed = ready & (ds < 0.5)                                        # TAKEDOWN AUTO : en position (proche+dos) ET non-vu
        if killed.any(): self.B.ddmg[killed.nonzero(as_tuple=True)[0], self.T] = 1.0
        prog = (self.prevdt - tdist) / self.S; self.prevdt = tdist
        alarm = self.alert > self.alarm
        success = killed & (~alarm)
        self.t = self.t + 1; timeout = self.t >= self.max_steps
        done = success | alarm | timeout
        rew = (2.5 * prog * undet                                          # approcher la cible non-vu (telescope : 0 si on stagne)
               - 1.5 * ds + 20.0 * success.float() - 4.0 * alarm.float() - 0.01)   # cone puni -> l'approche par le dos s'impose
        info = {"success": success, "alarm": alarm, "killed": killed, "detected": ds}
        self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info
