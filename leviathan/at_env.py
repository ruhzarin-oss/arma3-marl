#!/usr/bin/env python3
"""at_env.py — BRIQUE AT : détruire un véhicule en le frappant au FLANC/ARRIÈRE (blindage faible), pas de
face (la roquette ricoche). Manœuvrer vers un bon angle PUIS tirer ; roquettes limitées ; le véhicule
riposte si on est devant. A/B : voyant (voit l'orientation) flanque ; aveugle tire de face → ricoche.
Action : 0-7 = déplacement, 8 = tirer. Métrique = `destroyed`."""
import math, torch


class AtEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 45; self.speed = 8.0
        self.D = 8; self.obs_dim = 8
        ang = [k * 2 * math.pi / self.D for k in range(self.D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("mx", "my", "phi", "rockets", "valive", "alive", "t", "destroyed"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.phi[idx] = torch.rand(n, device=dev) * 2 * math.pi
        b = torch.rand(n, device=dev) * 2 * math.pi
        self.mx[idx] = 110 * torch.cos(self.phi[idx] + b)              # départ angle aléatoire à 110 m
        self.my[idx] = 110 * torch.sin(self.phi[idx] + b)
        self.rockets[idx] = 2.0; self.valive[idx] = 1.0; self.alive[idx] = 1.0
        self.t[idx] = 0; self.destroyed[idx] = 0.0

    def _geom(self):
        dist = torch.sqrt(self.mx ** 2 + self.my ** 2 + 1e-6)
        bem = torch.atan2(self.my, self.mx)
        alpha = torch.abs(((bem - self.phi + math.pi) % (2 * math.pi)) - math.pi)   # 0=face, π=arrière
        return dist, alpha

    def _obs(self):
        dist, alpha = self._geom()
        toV_x = -self.mx / dist; toV_y = -self.my / dist
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            toV_x, toV_y,
            torch.cos(self.phi) if not self.blind else z, torch.sin(self.phi) if not self.blind else z,
            (alpha / math.pi) if not self.blind else z,                # face(0)/arrière(1) = l'angle de tir
            (dist / 120.0).clamp(0, 1), self.rockets / 2.0, self.valive,
        ], dim=1)

    def step(self, action):
        dev = self.dev
        dist, alpha = self._geom()
        fire = (action == 8).float() * (self.rockets > 0).float() * self.valive
        mvi = action.clamp(0, self.D - 1)
        move = (action < 8).float()
        self.mx = self.mx + self.DX[mvi] * self.speed * move
        self.my = self.my + self.DY[mvi] * self.speed * move
        dist, alpha = self._geom()
        # efficacité du tir = fort au flanc/arrière (alpha>90°), nul de face
        eff = ((alpha - math.radians(50)) / math.radians(130)).clamp(0, 1)          # 0 à 50°, 1 à 180°
        kill = fire * (torch.rand(self.N, device=dev) < eff * 0.95).float()
        self.valive = self.valive * (1 - kill)
        self.rockets = (self.rockets - fire).clamp(min=0)
        wasted = fire * (alpha < math.radians(50)).float()             # tir de face = ricoché/gaspillé
        # le véhicule me canarde si je suis devant et proche
        infront = ((alpha < math.radians(50)) & (dist < 90)).float() * self.valive
        hit = (torch.rand(self.N, device=dev) < infront * 0.12)
        self.alive = self.alive * (~hit).float()
        self.destroyed = (self.valive == 0).float()
        r = kill * 10.0 - wasted * 1.5 - hit.float() * 4.0 - 0.04
        self.t += 1
        done = (self.valive == 0) | (self.alive == 0) | (self.t >= self.max_steps) | (dist > 250)
        info = {"destroyed": (self.valive == 0)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
