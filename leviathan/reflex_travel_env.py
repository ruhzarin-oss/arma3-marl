#!/usr/bin/env python3
"""reflex_travel_env.py — R5 en RÉGIME CALME : marcher vers un point en terrain ouvert, contourner les
obstacles, SANS combat. C'est la compétence manquante (le corps de combat ne voyage pas). Différent du
R5 qui plafonnait (champ DÉFENDU par 3 tireurs = impossible solo) : ici PAS de menace -> apprenable.

Perception = direction du but + distance + SENS DES OBSTACLES (8 secteurs). Action = déplacement (9).
A/B optionnel : blind=True met le sens des obstacles à 0 (le voyant doit contourner, l'aveugle se coince)."""
import math, torch

DEV_DEFAULT = "cuda:0"


class TravelEnv:
    def __init__(self, n, device, K=6, field=180.0, blind=False, seed=0):
        self.N = n; self.dev = device; self.K = K; self.field = field; self.blind = blind
        self.D = 8; self.max_steps = 70; self.speed = 4.0
        ang = [k * 2 * math.pi / self.D for k in range(self.D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        self.obs_dim = 2 + 1 + self.D + 1                            # but(2) + dist(1) + obstacles(8) + stuck(1)
        torch.manual_seed(seed)
        self._spawn(torch.arange(n, device=device))

    def _spawn(self, idx):
        n = idx.numel(); dev = self.dev
        if not hasattr(self, "px"):
            self.px = torch.zeros(self.N, device=dev); self.py = torch.zeros(self.N, device=dev)
            self.gx = torch.zeros(self.N, device=dev); self.gy = torch.zeros(self.N, device=dev)
            self.ox = torch.zeros(self.N, self.K, device=dev); self.oy = torch.zeros(self.N, self.K, device=dev)
            self.orad = torch.zeros(self.N, self.K, device=dev)
            self.t = torch.zeros(self.N, device=dev); self.stuck = torch.zeros(self.N, device=dev)
        self.px[idx] = torch.rand(n, device=dev) * self.field
        self.py[idx] = torch.rand(n, device=dev) * self.field
        a = torch.rand(n, device=dev) * 2 * math.pi; d = 110 + torch.rand(n, device=dev) * 60
        self.gx[idx] = (self.px[idx] + torch.cos(a) * d).clamp(5, self.field - 5)
        self.gy[idx] = (self.py[idx] + torch.sin(a) * d).clamp(5, self.field - 5)
        # obstacles entre le départ et le but (pour forcer le contournement)
        self.ox[idx] = torch.rand(n, self.K, device=dev) * self.field
        self.oy[idx] = torch.rand(n, self.K, device=dev) * self.field
        self.orad[idx] = 7 + torch.rand(n, self.K, device=dev) * 7
        self.t[idx] = 0; self.stuck[idx] = 0

    def _dist_goal(self):
        return torch.sqrt((self.gx - self.px) ** 2 + (self.gy - self.py) ** 2 + 1e-6)

    def _obs(self):
        dgx = self.gx - self.px; dgy = self.gy - self.py
        dg = torch.sqrt(dgx ** 2 + dgy ** 2 + 1e-6)
        gdir_x = dgx / dg; gdir_y = dgy / dg
        # sens des obstacles : par secteur, proximité du bord de l'obstacle le plus proche
        ox = self.ox - self.px[:, None]; oy = self.oy - self.py[:, None]                 # [N,K]
        od = torch.sqrt(ox ** 2 + oy ** 2 + 1e-6)
        edge = (od - self.orad).clamp(min=0.0)                                            # distance au BORD
        prox = (1.0 - edge / 60.0).clamp(0, 1)                                            # proche -> 1
        proj = ox[:, :, None] * self.DX[None, None, :] + oy[:, :, None] * self.DY[None, None, :]  # [N,K,D]
        sect = proj.argmax(-1)                                                            # [N,K]
        osense = torch.zeros(self.N, self.D, device=self.dev)
        osense.scatter_reduce_(1, sect, prox, reduce="amax", include_self=True)
        if self.blind: osense = osense * 0.0
        return torch.cat([gdir_x[:, None], gdir_y[:, None], (dg / self.field).clamp(0, 1)[:, None],
                          osense, self.stuck[:, None]], dim=1)

    def step(self, mv):
        old = self._dist_goal()
        mvi = mv.clamp(0, self.D)
        moving = (mvi > 0).float()
        dx = torch.where(mvi > 0, self.DX[(mvi - 1).clamp(0, self.D - 1)], torch.zeros_like(self.px))
        dy = torch.where(mvi > 0, self.DY[(mvi - 1).clamp(0, self.D - 1)], torch.zeros_like(self.py))
        nx = (self.px + dx * self.speed * moving).clamp(0, self.field)
        ny = (self.py + dy * self.speed * moving).clamp(0, self.field)
        # collision : si la nouvelle position entre dans un obstacle -> bloqué (reste, stuck=1)
        cx = nx[:, None] - self.ox; cy = ny[:, None] - self.oy
        inside = (torch.sqrt(cx ** 2 + cy ** 2 + 1e-6) < self.orad).any(1)
        self.px = torch.where(inside, self.px, nx); self.py = torch.where(inside, self.py, ny)
        self.stuck = inside.float()
        new = self._dist_goal()
        reached = new < 6.0
        r = (old - new) * 0.1                                                            # PROGRÈS = le moteur principal
        r = r + reached.float() * 10.0                                                   # arrivé
        r = r - inside.float() * 0.4                                                      # cogner un obstacle
        r = r - 0.02                                                                     # presse-toi (directness)
        self.t += 1
        done = reached | (self.t >= self.max_steps)
        info = {"reached": reached, "dist": new}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._spawn(idx)
        return self._obs(), r, done.float(), info
