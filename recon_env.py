"""RECON ENV v1 — drone INCARNÉ à perception active, en 2D (on empile l'altitude en v2).
Il se PILOTE (vx,vy) et RECONNAÎT via un capteur SIMULÉ à DEUX rayons :
  - rayon DÉTECTION (large) : repère un contact FLOU -> carte de contacts (sait OÙ aller).
  - rayon IDENTIFICATION (serré) : en restant dessus, la confiance monte -> identifié (verrouillé) à conf>=seuil.
        confiance ralentie par le CAMOUFLAGE (couvert local de la cible).
But = identifier TOUTES les cibles, vite -> apprend à BALAYER (couvrir le terrain) + CONFIRMER (rester sur un contact).

Réutilise le TERRAIN d'AssaultTerrain (cover) ; cibles étalées au hasard.
Transfert Arma : action [vx,vy] -> setVelocity UAV ; capteur -> knowsAbout/sensor components.
"""
import torch
from assault_terrain import AssaultTerrain
import terrain_gpu as TG


class ReconEnv:
    def __init__(self, num_envs, T=8, device="cuda:0", seed=0, G=6, field_frac=0.40,
                 det_R=46.0, id_R=22.0, vmax=22.0, conf_gain=0.5, conf_decay=0.12, recog_thr=0.8,
                 camo=0.5, max_steps=50, cov_bonus=0.10, contact_bonus=0.30):
        self.body = AssaultTerrain(num_envs=num_envs, A=2, D=2, device=device, seed=seed,
                                   shell_obs=False, team_obs=False, suffer=False, max_steps=max_steps)
        self.N = num_envs; self.T = T; self.dev = device; self.G = G; self.GG = G * G
        self.S = self.body.scale; self.FIELD = field_frac * self.S
        self.det_R = det_R; self.id_R = id_R; self.vmax = vmax
        self.conf_gain = conf_gain; self.conf_decay = conf_decay; self.recog_thr = recog_thr
        self.camo = camo; self.maxT = max_steps; self.cov_bonus = cov_bonus; self.contact_bonus = contact_bonus
        lin = torch.linspace(-self.FIELD, self.FIELD, G, device=device)
        gy, gx = torch.meshgrid(lin, lin, indexing="ij")
        self.cell = torch.stack([gx.reshape(-1), gy.reshape(-1)], dim=1)   # (GG,2)
        self.dx = torch.zeros(num_envs, device=device); self.dy = torch.zeros(num_envs, device=device)
        self.tpx = torch.zeros(num_envs, T, device=device); self.tpy = torch.zeros(num_envs, T, device=device)
        self.tcov = torch.zeros(num_envs, T, device=device)
        self.conf = torch.zeros(num_envs, T, device=device)
        self.recog = torch.zeros(num_envs, T, dtype=torch.bool, device=device)
        self.contacted = torch.zeros(num_envs, T, dtype=torch.bool, device=device)
        self.visit_grid = torch.zeros(num_envs, self.GG, device=device)
        self.contact_grid = torch.zeros(num_envs, self.GG, device=device)
        self.t = torch.zeros(num_envs, dtype=torch.long, device=device)
        self._alldone_prev = torch.zeros(num_envs, dtype=torch.bool, device=device)
        self.obs_dim = 3 + 2 * self.GG
        self.act_dim = 2

    def _cellflat(self, px, py):
        ix = (((px + self.FIELD) / (2 * self.FIELD)) * self.G).floor().clamp(0, self.G - 1).long()
        iy = (((py + self.FIELD) / (2 * self.FIELD)) * self.G).floor().clamp(0, self.G - 1).long()
        return iy * self.G + ix

    def _sense(self):
        ex = self.tpx - self.dx.unsqueeze(1); ey = self.tpy - self.dy.unsqueeze(1)  # (N,T)
        dist = torch.sqrt(ex * ex + ey * ey)
        # DÉTECTION (large) : contact flou
        det = dist < self.det_R
        det_q = (1.0 - dist / self.det_R).clamp(min=0.0) * det.float()
        new_contact = (det & (~self.contacted)).float().sum(1)
        self.contacted = self.contacted | det
        # IDENTIFICATION (serré) : confiance monte si on reste dessus, freinée par le camouflage
        in_id = dist < self.id_R
        center_q = (1.0 - dist / self.id_R).clamp(min=0.0) * in_id.float()
        camo_q = (1.0 - self.camo * self.tcov).clamp(min=0.05)
        gain = self.conf_gain * center_q * camo_q
        conf_prev = self.conf.clone()
        self.conf = (self.conf + gain - self.conf_decay * (~in_id).float()).clamp(0.0, 1.0)
        newly = (self.conf >= self.recog_thr) & (~self.recog)
        self.recog = self.recog | (self.conf >= self.recog_thr)
        dconf = (self.conf - conf_prev).clamp(min=0.0).sum(1)
        # carte de contacts (flou max par cellule) -> guide la navigation
        flat = self._cellflat(self.tpx, self.tpy)
        self.contact_grid.zero_()
        self.contact_grid.scatter_reduce_(1, flat, det_q, reduce="amax", include_self=True)
        return newly.float().sum(1), dconf, new_contact

    def _visit(self):                                            # marque la case sous le drone -> renvoie nb cases neuves
        c = self._cellflat(self.dx, self.dy).unsqueeze(1)        # (N,1)
        was = self.visit_grid.gather(1, c)                       # (N,1)
        self.visit_grid.scatter_(1, c, torch.ones_like(was))
        return (was < 0.5).float().squeeze(1)

    def _obs(self):
        scal = torch.stack([self.dx / self.FIELD, self.dy / self.FIELD, self.recog.float().mean(1)], dim=1)
        return torch.cat([scal, self.visit_grid, self.contact_grid], dim=1)

    def _spawn(self, idx):
        n = len(idx)
        self.tpx[idx] = (torch.rand(n, self.T, device=self.dev) * 2 - 1) * self.FIELD
        self.tpy[idx] = (torch.rand(n, self.T, device=self.dev) * 2 - 1) * self.FIELD
        self.tcov[idx] = TG.sample(self.body.cover, self.tpx[idx], self.tpy[idx], self.S).clamp(0, 1)
        self.conf[idx] = 0.0; self.recog[idx] = False; self.contacted[idx] = False
        self.visit_grid[idx] = 0.0; self.contact_grid[idx] = 0.0
        self.dx[idx] = (torch.rand(n, device=self.dev) * 2 - 1) * self.FIELD   # depart ALEATOIRE
        self.dy[idx] = (torch.rand(n, device=self.dev) * 2 - 1) * self.FIELD
        self.t[idx] = 0; self._alldone_prev[idx] = False

    def reset(self):
        self.body._reset(torch.arange(self.N, device=self.dev))
        self._spawn(torch.arange(self.N, device=self.dev))
        self._visit(); self._sense()
        return self._obs()

    def step(self, action):                                     # action (N,2) dans [-1,1]
        a = action.clamp(-1, 1)
        self.dx = (self.dx + a[:, 0] * self.vmax).clamp(-self.FIELD, self.FIELD)
        self.dy = (self.dy + a[:, 1] * self.vmax).clamp(-self.FIELD, self.FIELD)
        new_cells = self._visit()
        newly, dconf, new_contact = self._sense()
        self.t = self.t + 1
        allr = self.recog.all(1)
        first_all = allr & (~self._alldone_prev); self._alldone_prev = self._alldone_prev | allr
        rew = (3.0 * newly                       # IDENTIFIER une cible = le coeur
               + self.contact_bonus * new_contact   # repérer un contact (bootstrap navigation)
               + self.cov_bonus * new_cells      # BALAYER une case neuve (exploration, indep. de la vitesse)
               + 0.05 * dconf                    # rester sur un contact paie un peu
               - 0.02                            # cout/temps
               + 10.0 * first_all.float())       # tout identifie = bonus de vitesse
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
    def run(policy_fn, label, N=1024, steps=70, seed=1, T=8):
        e = ReconEnv(N, T=T, device=DEV, seed=seed); obs = e.reset(); rf = nr = ct = nep = 0.0
        for _ in range(steps):
            obs, rew, done, info = e.step(policy_fn(e, obs))
            if done.any():
                dm = done
                rf += info["recog_frac"][dm].sum().item(); nr += info["nrecog"][dm].sum().item()
                ct += info["contact_frac"][dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
        print("  %-26s | identifie %3.0f%% (%.1f/%d) | contacts %3.0f%% | %d ep"
              % (label, 100 * rf / max(nep, 1), nr / max(nep, 1), T, 100 * ct / max(nep, 1), nep))
    pe = ReconEnv(2, device=DEV); print("=== ReconEnv v1 (2D) : S=%.0f FIELD=%.0f obs=%d act=%d ===" % (pe.S, pe.FIELD, pe.obs_dim, pe.act_dim))
    run(lambda e, o: torch.rand(e.N, 2, device=DEV) * 2 - 1, "ALEATOIRE")
    def oracle(e, o):
        un = (~e.recog).float()
        ex = e.tpx - e.dx.unsqueeze(1); ey = e.tpy - e.dy.unsqueeze(1)
        d2 = ex * ex + ey * ey + (1 - un) * 1e12; j = d2.argmin(1)
        tx = torch.gather(e.tpx, 1, j.unsqueeze(1)).squeeze(1); ty = torch.gather(e.tpy, 1, j.unsqueeze(1)).squeeze(1)
        return torch.stack([((tx - e.dx) / e.vmax).clamp(-1, 1), ((ty - e.dy) / e.vmax).clamp(-1, 1)], dim=1)
    run(oracle, "ORACLE (va vers + reste)")
