"""StealthEnv — brique FURTIVITE. L'agent doit atteindre l'objectif (centre) SANS etre detecte.
Les gardes ont un CONE DE VUE (regardent vers l'exterieur) + portee + LOS. Detection = dans le cone.
Obs = coque couvert + vers-objectif + capteur de DETECTION (garde proche + exposition totale).
Recompense = avancer SEULEMENT si non-vu + grosse penalite si detecte + alarme si trop vu = mission ratee."""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


class StealthEnv:
    def __init__(self, num_envs, A=1, D=6, device="cuda:0", seed=0, replica=True,
                 replica_path="/home/younes/arma3-marl/replica.npz", fov_deg=25.0, drange=70.0,
                 alarm=3.0, max_steps=140):
        self.B = AssaultTerrain(num_envs=num_envs, A=A, D=D, device=device, seed=seed,
                                replica=replica, replica_path=replica_path, shell_obs=True, max_steps=10 ** 9)
        self.N, self.A, self.D, self.dev, self.S = num_envs, A, D, device, self.B.scale
        self.fov = math.radians(fov_deg); self.drange = drange; self.secure_r = 20.0
        self.alarm, self.max_steps = alarm, max_steps; self.n_actions = self.B.n_actions
        z = lambda: torch.zeros(num_envs, device=device)
        self.t, self.alert = z(), z()
        self.gface = torch.zeros(num_envs, D, device=device)
        self.prevd = torch.zeros(num_envs, A, device=device)
        self._reset(torch.arange(num_envs, device=device))
        self.obs_dim = self._obs().shape[-1]

    def _reset(self, ids):
        if ids.numel() == 0: return
        self.B._reset(ids)
        self.gface[ids] = torch.atan2(self.B.dpy[ids], self.B.dpx[ids])     # gardes regardent VERS L'EXTERIEUR
        self.alert[ids] = 0.0; self.t[ids] = 0.0
        self.prevd[ids] = torch.sqrt(self.B.apx[ids] ** 2 + self.B.apy[ids] ** 2)

    def reset(self):
        self._reset(torch.arange(self.N, device=self.dev)); return self._obs()

    def _detect(self):                                                     # -> (det bool (N,A), expo (N,A), ng dir/dist/expo)
        ax, ay, S, N, A = self.B.apx, self.B.apy, self.S, self.N, self.A
        det = torch.zeros(N, A, dtype=torch.bool, device=self.dev); expo = torch.zeros(N, A, device=self.dev)
        ng_d2 = torch.full((N, A), 1e18, device=self.dev); ng_e = torch.zeros(N, A, device=self.dev)
        ngx = torch.zeros(N, A, device=self.dev); ngy = torch.zeros(N, A, device=self.dev)
        for di in range(self.D):
            gx = self.B.dpx[:, di:di + 1]; gy = self.B.dpy[:, di:di + 1]; gf = self.gface[:, di:di + 1]
            dx = ax - gx; dy = ay - gy; dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
            ang = torch.atan2(dy, dx)
            off = (ang - gf).abs(); off = torch.minimum(off, 2 * math.pi - off)   # ecart au cap du garde
            los = self.B._losc(self.B.hm, gx.expand(N, A), gy.expand(N, A), ax, ay, S)
            inr = (dist < self.drange) & self.B._dalive()[:, di:di + 1]
            seen = (off < self.fov) & inr & (los > 0.5)
            det = det | seen
            e = (1 - off / self.fov).clamp(min=0) * inr.float() * los
            expo = torch.maximum(expo, e)
            closer = (dist * dist) < ng_d2
            ng_d2 = torch.where(closer, dist * dist, ng_d2); ngx = torch.where(closer, gx - ax, ngx); ngy = torch.where(closer, gy - ay, ngy)
            ng_e = torch.where(closer, e, ng_e)
        return det, expo, ngx, ngy, ng_e

    def _obs(self):
        S, ax, ay = self.S, self.B.apx, self.B.apy
        shell = self.B._cover_shell()
        d = torch.sqrt(ax ** 2 + ay ** 2) + 1e-6
        toobj = torch.stack([-ax / d, -ay / d, (d / S).clamp(max=2.0)], dim=2)   # vers le centre
        det, expo, ngx, ngy, nge = self._detect()
        ngd = torch.sqrt(ngx ** 2 + ngy ** 2) + 1e-6
        gobs = torch.stack([ngx / ngd, ngy / ngd, (ngd / S).clamp(max=2.0), nge], dim=2)   # garde proche + son exposition
        extra = torch.stack([expo, det.float(), self.B.admg], dim=2)            # exposition totale + vu + degats
        return torch.cat([shell, toobj, gobs, extra], dim=2)

    def step(self, acts):
        self.B.step(acts, auto_reset=False)
        det, expo, _, _, _ = self._detect()
        ds = det.float().squeeze(1) if self.A == 1 else det.float().mean(1)
        self.alert = self.alert + ds
        d = torch.sqrt(self.B.apx ** 2 + self.B.apy ** 2)
        dc = d.squeeze(1) if self.A == 1 else d.mean(1)
        prog = ((self.prevd - d).squeeze(1) if self.A == 1 else (self.prevd - d).mean(1)) / self.S
        self.prevd = d
        undet = 1.0 - ds
        alarm = self.alert > self.alarm
        success = (dc < self.secure_r) & (~alarm)
        self.t = self.t + 1; timeout = self.t >= self.max_steps
        done = success | alarm | timeout
        rew = 2.5 * prog * undet - 1.5 * ds + 15.0 * success.float() - 4.0 * alarm.float() - 0.03 * dc / self.S - 0.005
        info = {"success": success, "alarm": alarm, "detected": ds, "reached": dc < self.secure_r}
        self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info
