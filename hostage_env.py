import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


class HostageEnv:
    """Rescousse d'otage en ESCOUADE. Infil -> recup (agent vivant le + proche porte) -> exfil.
    TIER 1 : l'otage peut MOURIR (tir fratricide avant pickup, exposition aux gardes apres pickup),
    et le porteur se reprend (agent vivant le + proche)."""

    def __init__(self, num_envs, A=9, D=6, device="cuda:0", seed=0, replica=True,
                 replica_path="/home/younes/arma3-marl/replica.npz", hit=0.10, max_steps=140, ff_hit=0.05, exfil_hit=0.03):
        self.B = AssaultTerrain(num_envs=num_envs, A=A, D=D, device=device, seed=seed,
                                replica=replica, replica_path=replica_path, hit=hit,
                                shell_obs=True, max_steps=10**9)
        self.N, self.A, self.D, self.dev, self.S = num_envs, A, D, device, self.B.scale
        self.hit, self.max_steps, self.secure_r, self.fire_range = hit, max_steps, 18.0, self.B.fire_range
        self.ff_hit = ff_hit; self.exfil_hit = exfil_hit
        self.n_actions = self.B.n_actions
        z = lambda: torch.zeros(num_envs, device=device)
        self.hpx, self.hpy, self.hdmg, self.picked = z(), z(), z(), z()
        self.extx, self.exty, self.t, self.prevdh, self.prevde = z(), z(), z(), z(), z()
        self._reset(torch.arange(num_envs, device=device))
        self.obs_dim = self._obs().shape[-1]

    def _reset(self, ids):
        if ids.numel() == 0: return
        self.B._reset(ids)
        self.hpx[ids] = 0.0; self.hpy[ids] = 0.0; self.hdmg[ids] = 0.0; self.picked[ids] = 0.0; self.t[ids] = 0.0
        self.extx[ids] = self.B.apx[ids].mean(1); self.exty[ids] = self.B.apy[ids].mean(1)
        self.prevdh[ids] = torch.sqrt(self.B.apx[ids] ** 2 + self.B.apy[ids] ** 2).min(1).values
        cx = self.B.apx[ids].mean(1); cy = self.B.apy[ids].mean(1)
        self.prevde[ids] = torch.sqrt((cx - self.extx[ids]) ** 2 + (cy - self.exty[ids]) ** 2)

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
        tx = ax[:, None, :] - ax[:, :, None]; ty = ay[:, None, :] - ay[:, :, None]
        eye = torch.eye(self.A, dtype=torch.bool, device=self.dev)[None]
        td2 = torch.where(eye | ~self.B._aalive()[:, None, :], torch.full_like(tx, 1e18), tx * tx + ty * ty); jm = td2.argmin(2)
        tdx = torch.gather(tx, 2, jm.unsqueeze(2)).squeeze(2); tdy = torch.gather(ty, 2, jm.unsqueeze(2)).squeeze(2)
        td = torch.sqrt(tdx ** 2 + tdy ** 2) + 1e-6
        tobs = torch.stack([tdx / td, tdy / td, (td / S).clamp(max=2.0)], dim=2)
        pk = self.picked[:, None, None].expand(self.N, self.A, 1)
        hh = self.hdmg[:, None, None].expand(self.N, self.A, 1)
        oh = self.B.admg.unsqueeze(2)
        return torch.cat([shell, toh, toe, gobs, tobs, pk, hh, oh], dim=2)

    def step(self, acts):
        a2 = acts if acts.dim() == 2 else acts.squeeze(-1)
        self.B.step(acts, auto_reset=False)
        ax, ay, S, N, A = self.B.apx, self.B.apy, self.S, self.N, self.A
        alive = self.B._aalive()
        # --- porteur = agent VIVANT le plus proche (reprise) ---
        big = torch.full((N, A), 1e9, device=self.dev)
        dh_all = torch.where(alive, torch.sqrt((ax - self.hpx[:, None]) ** 2 + (ay - self.hpy[:, None]) ** 2), big)
        dh = dh_all.min(1).values; carrier = dh_all.argmin(1)
        near = dh < self.secure_r
        newpick = (near & (self.picked < 0.5)).float()
        self.picked = torch.maximum(self.picked, near.float())
        follow = (self.picked > 0.5) & near
        cax = torch.gather(ax, 1, carrier.unsqueeze(1)).squeeze(1); cay = torch.gather(ay, 1, carrier.unsqueeze(1)).squeeze(1)
        self.hpx = torch.where(follow, cax, self.hpx); self.hpy = torch.where(follow, cay, self.hpy)
        # --- TIER 1 : degats a l'otage ---
        # (a) tir fratricide : agent vivant qui SUPPRIME (9) avec LOS+portee vers l'otage -> le touche (avant pickup)
        losH = self.B._losc(self.B.hm, ax, ay, self.hpx[:, None].expand(N, A), self.hpy[:, None].expand(N, A), S)
        distH = torch.sqrt((ax - self.hpx[:, None]) ** 2 + (ay - self.hpy[:, None]) ** 2)
        ff = (((a2 == 9) & alive).float() * losH * (distH < self.fire_range).float()).sum(1)
        # (b) exposition exfil : gardes vivants LOS+portee touchent l'otage PORTE
        hg = torch.zeros(N, device=self.dev)
        for di in range(self.D):
            gx = self.B.dpx[:, di]; gy = self.B.dpy[:, di]
            losG = self.B._losc(self.B.hm, gx.unsqueeze(1), gy.unsqueeze(1), self.hpx.unsqueeze(1), self.hpy.unsqueeze(1), S)[:, 0]
            distG = torch.sqrt((gx - self.hpx) ** 2 + (gy - self.hpy) ** 2)
            hg += self.exfil_hit * losG * self.B._dalive()[:, di].float() * (distG < self.fire_range).float()
        dmg_now = self.ff_hit * ff * (1.0 - self.picked) + hg * self.picked   # degats otage CE pas (pente dense)
        self.hdmg = (self.hdmg + dmg_now).clamp(max=1.0)
        # --- statut ---
        de = torch.sqrt((self.hpx - self.extx) ** 2 + (self.hpy - self.exty) ** 2)
        adead = self.B.admg > 0.7; squad_wipe = adead.all(1); hdead = self.hdmg > 0.7
        success = (self.picked > 0.5) & (de < self.secure_r) & (~squad_wipe) & (~hdead)
        self.t = self.t + 1; timeout = self.t >= self.max_steps
        done = success | squad_wipe | hdead | timeout
        # --- RECOMPENSE PARTAGEE (v1, rescousse = optimum) + PRESSION DE TEMPS ---
        fail = done & (~success)                                                                # episode fini SANS rescousse
        prog_h = (self.prevdh - dh) / S * (1.0 - self.picked); prog_e = (self.prevde - de) / S * self.picked
        team = (0.5 * prog_h + 0.5 * prog_e + 3.0 * newpick + 10.0 * success.float()
                - 2.0 * dmg_now - 1.0 * hdead.float()                                           # Tier-1 (inerte a la base)
                - 0.01 * (1.0 - self.picked) - 3.0 * fail.float() - 0.005)                      # urgence + echec coute
        self.prevdh = dh; self.prevde = de
        rew = team[:, None].expand(N, A) - 0.2 * adead.float()
        info = {"success": success, "hdead": hdead, "squad_wipe": squad_wipe, "picked": self.picked > 0.5}
        self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info
