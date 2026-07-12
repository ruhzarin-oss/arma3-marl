#!/usr/bin/env python3
"""flank_env.py — BRIQUE FLANC : atteindre un point DERRIÈRE l'ennemi en évitant son CÔNE FRONTAL létal,
au lieu de foncer dedans. Objectif clair (point arrière) + reward de distance (apprend vite), cône létal
force le contournement. A/B : voyant (sait où est l'arrière + le cône) contourne ; aveugle fonce → meurt."""
import math, torch


class FlankEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 60; self.speed = 7.0
        self.D = 8; self.obs_dim = 8
        ang = [k * 2 * math.pi / self.D for k in range(self.D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("mx", "my", "phi", "rx", "ry", "t", "alive", "reached", "supp"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.phi[idx] = torch.rand(n, device=dev) * 2 * math.pi
        beta = torch.rand(n, device=dev) * 2 * math.pi                 # angle de départ ALÉATOIRE autour de l'ennemi
        self.mx[idx] = 120 * torch.cos(self.phi[idx] + beta)           # (parfois près de l'arrière = facile -> curriculum)
        self.my[idx] = 120 * torch.sin(self.phi[idx] + beta)
        self.rx[idx] = -70 * torch.cos(self.phi[idx])                  # point ARRIÈRE : 70 m derrière l'ennemi
        self.ry[idx] = -70 * torch.sin(self.phi[idx])
        self.t[idx] = 0; self.alive[idx] = 1.0; self.reached[idx] = 0.0; self.supp[idx] = 0.0

    def _geom(self):
        dist = torch.sqrt(self.mx ** 2 + self.my ** 2 + 1e-6)         # distance à l'ennemi (origine)
        bem = torch.atan2(self.my, self.mx)
        alpha = torch.abs(((bem - self.phi + math.pi) % (2 * math.pi)) - math.pi)   # 0=front, π=arrière
        drear = torch.sqrt((self.mx - self.rx) ** 2 + (self.my - self.ry) ** 2 + 1e-6)
        return dist, alpha, drear

    def _obs(self):
        dist, alpha, drear = self._geom()
        rdir_x = (self.rx - self.mx) / drear; rdir_y = (self.ry - self.my) / drear   # vers l'ARRIÈRE (le secret)
        toE_x = -self.mx / dist; toE_y = -self.my / dist                              # vers l'ennemi (connu même aveugle)
        in_cone = ((alpha < math.radians(60)) & (dist < 100)).float()
        z = torch.zeros(self.N, device=self.dev)
        o = torch.stack([
            rdir_x if not self.blind else z, rdir_y if not self.blind else z,   # direction de l'arrière
            in_cone if not self.blind else z,                                   # suis-je dans le cône mortel
            (alpha / math.pi) if not self.blind else z,                         # front(0)/arrière(1)
            toE_x, toE_y,                                                        # l'ennemi (connu)
            (dist / 150.0).clamp(0, 1),
            self.supp,
        ], dim=1)
        return o

    def step(self, mv):
        dev = self.dev
        _, _, drear0 = self._geom()
        self.supp = (torch.rand(self.N, device=dev) < 0.2).float()
        mvi = mv.clamp(0, self.D - 1)
        self.mx = self.mx + self.DX[mvi] * self.speed
        self.my = self.my + self.DY[mvi] * self.speed
        dist, alpha, drear = self._geom()
        in_cone = ((alpha < math.radians(60)) & (dist < 100)).float()
        exposed = 1 - self.supp
        hit = (torch.rand(self.N, device=dev) < in_cone * exposed * 0.45)
        self.alive = self.alive * (~hit).float()
        reached = (drear < 32).float() * self.alive
        self.reached = reached
        r = (drear0 - drear) * 0.15                                    # PROGRÈS vers l'arrière (signal dense)
        r = r + reached * 10.0 - in_cone * exposed * 0.4 - hit.float() * 8.0 - 0.02
        self.t += 1
        done = (reached > 0) | (self.alive == 0) | (self.t >= self.max_steps) | (dist > 280)
        info = {"reached": reached.bool(), "alive": self.alive}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
