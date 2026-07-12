"""RECON SWARM ENV — K drones en perception active COOPERATIVE (MARL, politique partagee).
Casse le mur d'echelle du mono-drone : plusieurs drones se REPARTISSENT le terrain.

- Image COMMUNE (datalink) : grille de visite + grille de contacts partagees par l'equipe.
- Coordination : chaque drone voit la position des AUTRES (grille d'equipe) -> division du travail emergente.
- Capteur simule par drone : 2 rayons (detection large = contacts flous / identification serree = rester dessus),
  identification freinee par le camouflage. Une cible identifiee par N'IMPORTE quel drone compte.
- Recompense d'EQUIPE (cooperatif) : identifier toutes les cibles, vite.

Cas K=1 == le mono-drone d'avant. Transfert Arma : actions [vx,vy] par UAV ; capteur -> knowsAbout.
"""
import torch
from assault_terrain import AssaultTerrain
import terrain_gpu as TG


class ReconSwarmEnv:
    def __init__(self, num_envs, K=4, T=12, device="cuda:0", seed=0, G=6, field_frac=0.40,
                 det_R=46.0, id_R=22.0, vmax=22.0, conf_gain=0.5, conf_decay=0.12, recog_thr=0.8,
                 camo=0.5, max_steps=50, cov_bonus=0.10, contact_bonus=0.30):
        self.body = AssaultTerrain(num_envs=num_envs, A=2, D=2, device=device, seed=seed,
                                   shell_obs=False, team_obs=False, suffer=False, max_steps=max_steps)
        self.N = num_envs; self.K = K; self.T = T; self.dev = device; self.G = G; self.GG = G * G
        self.S = self.body.scale; self.FIELD = field_frac * self.S
        self.det_R = det_R; self.id_R = id_R; self.vmax = vmax
        self.conf_gain = conf_gain; self.conf_decay = conf_decay; self.recog_thr = recog_thr
        self.camo = camo; self.maxT = max_steps; self.cov_bonus = cov_bonus; self.contact_bonus = contact_bonus
        lin = torch.linspace(-self.FIELD, self.FIELD, G, device=device)
        gy, gx = torch.meshgrid(lin, lin, indexing="ij")
        self.cell = torch.stack([gx.reshape(-1), gy.reshape(-1)], dim=1)
        self.dx = torch.zeros(num_envs, K, device=device); self.dy = torch.zeros(num_envs, K, device=device)
        self.tpx = torch.zeros(num_envs, T, device=device); self.tpy = torch.zeros(num_envs, T, device=device)
        self.tcov = torch.zeros(num_envs, T, device=device)
        self.conf = torch.zeros(num_envs, T, device=device)
        self.recog = torch.zeros(num_envs, T, dtype=torch.bool, device=device)
        self.contacted = torch.zeros(num_envs, T, dtype=torch.bool, device=device)
        self.visit_grid = torch.zeros(num_envs, self.GG, device=device)
        self.contact_grid = torch.zeros(num_envs, self.GG, device=device)
        self.t = torch.zeros(num_envs, dtype=torch.long, device=device)
        self._alldone_prev = torch.zeros(num_envs, dtype=torch.bool, device=device)
        self.obs_dim = 3 + 3 * self.GG          # own xy + frac + visit + contact + teammates
        self.act_dim = 2

    def _cellflat(self, px, py):
        ix = (((px + self.FIELD) / (2 * self.FIELD)) * self.G).floor().clamp(0, self.G - 1).long()
        iy = (((py + self.FIELD) / (2 * self.FIELD)) * self.G).floor().clamp(0, self.G - 1).long()
        return iy * self.G + ix

    def _sense(self):
        ex = self.tpx.unsqueeze(1) - self.dx.unsqueeze(2)         # (N,K,T)
        ey = self.tpy.unsqueeze(1) - self.dy.unsqueeze(2)
        dist = torch.sqrt(ex * ex + ey * ey)
        det = dist < self.det_R                                   # (N,K,T)
        det_any = det.any(1)                                      # (N,T)
        det_q = ((1.0 - dist / self.det_R).clamp(min=0.0) * det.float()).amax(1)   # (N,T) meilleur
        new_contact = (det_any & (~self.contacted)).float().sum(1)
        self.contacted = self.contacted | det_any
        in_id = dist < self.id_R                                  # (N,K,T)
        center_q = ((1.0 - dist / self.id_R).clamp(min=0.0) * in_id.float()).amax(1)   # (N,T) meilleur drone
        camo_q = (1.0 - self.camo * self.tcov).clamp(min=0.05)
        gain = self.conf_gain * center_q * camo_q
        any_id = in_id.any(1)                                     # (N,T) un drone confirme ?
        conf_prev = self.conf.clone()
        self.conf = (self.conf + gain - self.conf_decay * (~any_id).float()).clamp(0.0, 1.0)
        newly = (self.conf >= self.recog_thr) & (~self.recog)
        self.recog = self.recog | (self.conf >= self.recog_thr)
        dconf = (self.conf - conf_prev).clamp(min=0.0).sum(1)
        flat = self._cellflat(self.tpx, self.tpy)                 # (N,T)
        self.contact_grid.zero_()
        self.contact_grid.scatter_reduce_(1, flat, det_q, reduce="amax", include_self=True)
        return newly.float().sum(1), dconf, new_contact

    def _visit(self):                                            # grille partagee ; renvoie nb cases neuves (N,)
        c = self._cellflat(self.dx, self.dy)                      # (N,K)
        touched = torch.zeros_like(self.visit_grid)
        touched.scatter_(1, c, 1.0)                              # cellules touchees ce pas
        newly = ((touched > 0.5) & (self.visit_grid < 0.5)).float().sum(1)
        self.visit_grid = torch.maximum(self.visit_grid, touched)
        return newly

    def _teammate_grids(self):                                  # (N,K,GG) : densite des AUTRES drones
        c = self._cellflat(self.dx, self.dy)                      # (N,K)
        team = torch.zeros(self.N, self.GG, device=self.dev)
        team.scatter_add_(1, c, torch.ones_like(self.dx))        # densite totale (N,GG)
        own = torch.zeros(self.N, self.K, self.GG, device=self.dev)
        own.scatter_(2, c.unsqueeze(2), 1.0)
        return (team.unsqueeze(1) - own).clamp(min=0.0)          # (N,K,GG)

    def _obs(self):
        own = torch.stack([self.dx / self.FIELD, self.dy / self.FIELD], dim=2)        # (N,K,2)
        frac = self.recog.float().mean(1).view(self.N, 1, 1).expand(self.N, self.K, 1)
        vis = self.visit_grid.unsqueeze(1).expand(self.N, self.K, self.GG)
        con = self.contact_grid.unsqueeze(1).expand(self.N, self.K, self.GG)
        team = self._teammate_grids()
        return torch.cat([own, frac, vis, con, team], dim=2)     # (N,K,obs_dim)

    def _spawn(self, idx):
        n = len(idx)
        self.tpx[idx] = (torch.rand(n, self.T, device=self.dev) * 2 - 1) * self.FIELD
        self.tpy[idx] = (torch.rand(n, self.T, device=self.dev) * 2 - 1) * self.FIELD
        self.tcov[idx] = TG.sample(self.body.cover, self.tpx[idx], self.tpy[idx], self.S).clamp(0, 1)
        self.conf[idx] = 0.0; self.recog[idx] = False; self.contacted[idx] = False
        self.visit_grid[idx] = 0.0; self.contact_grid[idx] = 0.0
        self.dx[idx] = (torch.rand(n, self.K, device=self.dev) * 2 - 1) * self.FIELD
        self.dy[idx] = (torch.rand(n, self.K, device=self.dev) * 2 - 1) * self.FIELD
        self.t[idx] = 0; self._alldone_prev[idx] = False

    def reset(self):
        self.body._reset(torch.arange(self.N, device=self.dev))
        self._spawn(torch.arange(self.N, device=self.dev))
        self._visit(); self._sense()
        return self._obs()

    def step(self, action):                                     # action (N,K,2) dans [-1,1]
        a = action.clamp(-1, 1)
        self.dx = (self.dx + a[..., 0] * self.vmax).clamp(-self.FIELD, self.FIELD)
        self.dy = (self.dy + a[..., 1] * self.vmax).clamp(-self.FIELD, self.FIELD)
        new_cells = self._visit()
        newly, dconf, new_contact = self._sense()
        self.t = self.t + 1
        allr = self.recog.all(1)
        first_all = allr & (~self._alldone_prev); self._alldone_prev = self._alldone_prev | allr
        rew = (3.0 * newly + self.contact_bonus * new_contact + self.cov_bonus * new_cells
               + 0.05 * dconf - 0.02 + 10.0 * first_all.float())        # (N,) recompense d'EQUIPE
        done = allr | (self.t >= self.maxT)
        info = {"recog_frac": self.recog.float().mean(1), "all": allr, "nrecog": self.recog.float().sum(1),
                "contact_frac": self.contacted.float().mean(1)}
        return self._obs(), rew, done, info

    def reset_done(self, done):
        idx = done.nonzero(as_tuple=True)[0]
        if len(idx) == 0: return
        self.body._reset(idx); self._spawn(idx); self._visit(); self._sense()


if __name__ == "__main__":
    DEV = "cuda:0"
    def run(policy_fn, label, K, N=1024, steps=70, seed=1, T=12, ff=0.40):
        e = ReconSwarmEnv(N, K=K, T=T, device=DEV, seed=seed, field_frac=ff); obs = e.reset()
        rf = nr = ct = nep = 0.0
        for _ in range(steps):
            obs, rew, done, info = e.step(policy_fn(e, obs))
            if done.any():
                dm = done
                rf += info["recog_frac"][dm].sum().item(); nr += info["nrecog"][dm].sum().item()
                ct += info["contact_frac"][dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
        print("  %-30s | identifie %3.0f%% (%.1f/%d) | contacts %3.0f%% | %d ep"
              % (label, 100 * rf / max(nep, 1), nr / max(nep, 1), T, 100 * ct / max(nep, 1), nep))
    pe = ReconSwarmEnv(2, device=DEV); print("=== ReconSwarmEnv : S=%.0f obs=%d act=%d ===" % (pe.S, pe.obs_dim, pe.act_dim))
    def oracle(e, o):                            # chaque drone -> cible non-identifiee la + proche de LUI
        un = (~e.recog).float().unsqueeze(1)                                 # (N,1,T)
        ex = e.tpx.unsqueeze(1) - e.dx.unsqueeze(2); ey = e.tpy.unsqueeze(1) - e.dy.unsqueeze(2)  # (N,K,T)
        d2 = ex * ex + ey * ey + (1 - un) * 1e12
        j = d2.argmin(2)                                                     # (N,K)
        tx = torch.gather(e.tpx, 1, j); ty = torch.gather(e.tpy, 1, j)       # (N,K)
        return torch.stack([((tx - e.dx) / e.vmax).clamp(-1, 1), ((ty - e.dy) / e.vmax).clamp(-1, 1)], dim=2)
    run(lambda e, o: torch.rand(e.N, e.K, 2, device=DEV) * 2 - 1, "ALEATOIRE K=4 (grand terrain)", K=4)
    run(oracle, "ORACLE K=1 (grand terrain)", K=1)
    run(oracle, "ORACLE K=4 (grand terrain)", K=4)
