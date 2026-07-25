"""EscortEnv — entraine le skill ESCORTE (mono-agent). Un otage PORTE file vers la sortie (scripte) ;
des gardes le canardent ; l'escort doit le garder VIVANT en suppressant les gardes menacants.
Obs = 29 (compatible d6, pour brancher dans le chef). Action = 10 (caps + HOLD + SUPPRESS)."""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


class EscortEnv:
    def __init__(self, num_envs, A=1, D=6, device="cuda:0", seed=0, replica=True,
                 replica_path="/home/younes/arma3-marl/replica.npz", exfil_hit=0.05, max_steps=120):
        self.B = AssaultTerrain(num_envs=num_envs, A=A, D=D, device=device, seed=seed,
                                replica=replica, replica_path=replica_path, shell_obs=True, max_steps=10 ** 9)
        self.N, self.A, self.D, self.dev, self.S = num_envs, A, D, device, self.B.scale
        self.exfil_hit, self.max_steps, self.secure_r, self.fire_range = exfil_hit, max_steps, 25.0, self.B.fire_range
        self.carry = self.B.move * 0.4
        self.n_actions = self.B.n_actions
        z = lambda: torch.zeros(num_envs, device=device)
        self.hpx, self.hpy, self.hdmg, self.extx, self.exty, self.t = z(), z(), z(), z(), z(), z()
        self._reset(torch.arange(num_envs, device=device))
        self.obs_dim = self._obs().shape[-1]

    def _reset(self, ids):
        if ids.numel() == 0: return
        self.B._reset(ids)
        self.hpx[ids] = 0.0; self.hpy[ids] = 0.0; self.hdmg[ids] = 0.0; self.t[ids] = 0.0
        self.extx[ids] = 0.0; self.exty[ids] = -self.B.R_spawn          # sortie plein sud
        self.B.apx[ids] = torch.randn(len(ids), self.A, device=self.dev) * 8   # escort pres de l'otage
        self.B.apy[ids] = torch.randn(len(ids), self.A, device=self.dev) * 8

    def reset(self):
        self._reset(torch.arange(self.N, device=self.dev)); return self._obs()

    def _obs(self):
        S, ax, ay = self.S, self.B.apx, self.B.apy
        shell = self.B._cover_shell()
        dhx = self.hpx[:, None] - ax; dhy = self.hpy[:, None] - ay; dh = torch.sqrt(dhx ** 2 + dhy ** 2) + 1e-6
        toh = torch.stack([dhx / dh, dhy / dh, (dh / S).clamp(max=2.0)], dim=2)
        dex = self.extx[:, None] - ax; dey = self.exty[:, None] - ay; de = torch.sqrt(dex ** 2 + dey ** 2) + 1e-6
        toe = torch.stack([dex / de, dey / de, (de / S).clamp(max=2.0)], dim=2)
        gx = self.B.dpx[:, None, :] - ax[:, :, None]; gy = self.B.dpy[:, None, :] - ay[:, :, None]
        gd2 = torch.where(self.B._dalive()[:, None, :], gx * gx + gy * gy, torch.full_like(gx, 1e18)); km = gd2.argmin(2)
        bx = torch.gather(self.B.dpx[:, None, :].expand(self.N, self.A, self.D), 2, km.unsqueeze(2)).squeeze(2)
        by = torch.gather(self.B.dpy[:, None, :].expand(self.N, self.A, self.D), 2, km.unsqueeze(2)).squeeze(2)
        gdx = bx - ax; gdy = by - ay; gd = torch.sqrt(gdx ** 2 + gdy ** 2) + 1e-6
        los = self.B._losc(self.B.hm, ax, ay, bx, by, S)
        gobs = torch.stack([gdx / gd, gdy / gd, (gd / S).clamp(max=2.0), los], dim=2)
        tobs = torch.zeros(self.N, self.A, 3, device=self.dev)
        pk = torch.ones(self.N, self.A, 1, device=self.dev)
        hh = self.hdmg[:, None, None].expand(self.N, self.A, 1)
        oh = self.B.admg.unsqueeze(2)
        return torch.cat([shell, toh, toe, gobs, tobs, pk, hh, oh], dim=2)

    def step(self, acts):
        a2 = acts if acts.dim() == 2 else acts.squeeze(-1)
        self.B.step(acts, auto_reset=False)                 # bouge l'escort, suppresse les gardes vises (dsupp)
        N, S = self.N, self.S
        dx = self.extx - self.hpx; dy = self.exty - self.hpy; dd = torch.sqrt(dx ** 2 + dy ** 2) + 1e-6
        self.hpx = self.hpx + self.carry * dx / dd; self.hpy = self.hpy + self.carry * dy / dd   # otage porte file vers la sortie
        dmg = torch.zeros(N, device=self.dev)
        for di in range(self.D):
            gx = self.B.dpx[:, di]; gy = self.B.dpy[:, di]
            los = self.B._losc(self.B.hm, gx.unsqueeze(1), gy.unsqueeze(1), self.hpx.unsqueeze(1), self.hpy.unsqueeze(1), S)[:, 0]
            dist = torch.sqrt((gx - self.hpx) ** 2 + (gy - self.hpy) ** 2)
            active = self.B._dalive()[:, di].float() * (self.B.dsupp[:, di] < 0.5).float() * (dist < self.fire_range).float() * los
            dmg = dmg + self.exfil_hit * active
        self.hdmg = (self.hdmg + dmg).clamp(max=1.0)
        supp = ((a2 == 9) & self.B._aalive()).float().squeeze(1)        # A=1 : suppression de l'escort
        de = torch.sqrt((self.hpx - self.extx) ** 2 + (self.hpy - self.exty) ** 2)
        adead = (self.B.admg.squeeze(1) > 0.7)
        hdead = self.hdmg > 0.7
        success = (de < self.secure_r) & (~hdead)          # otage vivant a la sortie (l'escort peut tomber)
        self.t = self.t + 1; timeout = self.t >= self.max_steps
        done = success | hdead | timeout          # l'episode suit l'OTAGE ; l'escort peut tomber sans finir l'episode
        rew = (-2.0 * dmg + 0.3 * supp + 5.0 * success.float() - 0.2 * adead.float() - 0.01)
        info = {"success": success, "hdead": hdead, "adead": adead, "hdmg": self.hdmg.clone()}
        self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info
