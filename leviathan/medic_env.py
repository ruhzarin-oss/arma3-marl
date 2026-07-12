#!/usr/bin/env python3
"""medic_env.py — BRIQUE MÉDIC : rejoindre les coéquipiers À TERRE et les RANIMER (la force ne fond pas).
Ranimation AUTO en atteignant le tombé (<12 m) → on enchaîne. A/B : voyant (voit où sont les tombés) y va ;
aveugle erre. Action : déplacement 8 dir. Métrique = `revived` (fraction des tombés ranimés)."""
import math, torch


class MedicEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 55; self.speed = 9.0; self.field = 220.0
        self.D = 8; self.obs_dim = 4; self.POSS = 4
        ang = [k * 2 * math.pi / self.D for k in range(self.D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("mx", "my", "dx", "dy", "threat", "revived", "t", "alive"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.mx[idx] = 0.0; self.my[idx] = 0.0
        self._newdowned(idx)
        self.revived[idx] = 0.0; self.t[idx] = 0; self.alive[idx] = 1.0

    def _newdowned(self, idx):
        n = idx.numel(); dev = self.dev
        a = torch.rand(n, device=dev) * 2 * math.pi; r = 60 + torch.rand(n, device=dev) * 90
        self.dx[idx] = r * torch.cos(a); self.dy[idx] = r * torch.sin(a)
        self.threat[idx] = (torch.rand(n, device=dev) < 0.4).float()

    def _obs(self):
        ddx = self.dx - self.mx; ddy = self.dy - self.my
        d = torch.sqrt(ddx ** 2 + ddy ** 2 + 1e-6)
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            (ddx / d) if not self.blind else z, (ddy / d) if not self.blind else z,   # direction du tombé (le secret)
            (d / self.field).clamp(0, 1) if not self.blind else z,
            self.threat,
        ], dim=1)

    def step(self, action):
        dev = self.dev
        dprev = torch.sqrt((self.dx - self.mx) ** 2 + (self.dy - self.my) ** 2 + 1e-6)
        mvi = action.clamp(0, self.D - 1)
        self.mx = self.mx + self.DX[mvi] * self.speed
        self.my = self.my + self.DY[mvi] * self.speed
        d = torch.sqrt((self.dx - self.mx) ** 2 + (self.dy - self.my) ** 2 + 1e-6)
        revive = (d < 12).float()                                      # ranime AUTO en atteignant le tombé
        near_danger = (d < 40).float() * self.threat
        hit = (torch.rand(self.N, device=dev) < near_danger * 0.05)
        self.alive = self.alive * (~hit).float()
        self.revived = self.revived + revive
        r = revive * 10.0 + (dprev - d) * 0.05 - hit.float() * 3.0 - 0.03
        idx_rev = torch.where(revive > 0)[0]
        if idx_rev.numel() > 0: self._newdowned(idx_rev)
        self.t += 1
        done = (self.revived >= self.POSS) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"revived": (self.revived / self.POSS).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
