#!/usr/bin/env python3
"""recup_env.py — BRIQUE RÉCUP BLESSÉS : ramener un blessé au couvert en CONTOURNANT la zone de feu (porter
= lent + vulnérable). Objectif = le point de couvert ; une zone létale à éviter (le feu ennemi). PRIME :
arriver au couvert avec le blessé. A/B : voyant voit la zone de feu ; aveugle passe dedans → perd le blessé.
Action : déplacement 8 dir. Métrique = `saved`."""
import math, torch


class RecupEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 50; self.speed = 5.0; self.field = 200.0
        self.D = 8; self.obs_dim = 7
        ang = [k * 2 * math.pi / self.D for k in range(self.D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("mx", "my", "cx", "cy", "zx", "zy", "alive", "t", "saved"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.mx[idx] = (torch.rand(n, device=dev) - 0.5) * 180         # départ ALÉATOIRE (curriculum : parfois près du couvert)
        self.my[idx] = (torch.rand(n, device=dev) - 0.5) * 180
        ac = torch.rand(n, device=dev) * 2 * math.pi
        self.cx[idx] = 110 * torch.cos(ac); self.cy[idx] = 110 * torch.sin(ac)   # couvert
        self.zx[idx] = 55 * torch.cos(ac) + (torch.rand(n, device=dev) - 0.5) * 50   # zone de feu ~ sur le chemin
        self.zy[idx] = 55 * torch.sin(ac) + (torch.rand(n, device=dev) - 0.5) * 50
        self.alive[idx] = 1.0; self.t[idx] = 0; self.saved[idx] = 0.0

    def _obs(self):
        dcx = self.cx - self.mx; dcy = self.cy - self.my; dc = torch.sqrt(dcx ** 2 + dcy ** 2 + 1e-6)
        dzx = self.zx - self.mx; dzy = self.zy - self.my; dz = torch.sqrt(dzx ** 2 + dzy ** 2 + 1e-6)
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            dcx / dc, dcy / dc, (dc / self.field).clamp(0, 1),          # le couvert (le but)
            (dzx / dz) if not self.blind else z, (dzy / dz) if not self.blind else z,   # la zone de feu (le secret)
            (dz / self.field).clamp(0, 1) if not self.blind else z,
            self.alive,
        ], dim=1)

    def step(self, action):
        dev = self.dev
        dc0 = torch.sqrt((self.cx - self.mx) ** 2 + (self.cy - self.my) ** 2 + 1e-6)
        mvi = action.clamp(0, self.D - 1)
        self.mx = self.mx + self.DX[mvi] * self.speed
        self.my = self.my + self.DY[mvi] * self.speed
        dc = torch.sqrt((self.cx - self.mx) ** 2 + (self.cy - self.my) ** 2 + 1e-6)
        dz = torch.sqrt((self.zx - self.mx) ** 2 + (self.zy - self.my) ** 2 + 1e-6)
        in_fire = (dz < 35).float()                                    # dans la zone de feu = vulnérable (on porte)
        hit = (torch.rand(self.N, device=dev) < in_fire * 0.14)
        self.alive = self.alive * (~hit).float()
        self.saved = ((dc < 18) & (self.alive > 0)).float()
        r = (dc0 - dc) * 0.06 + self.saved * 10.0 - hit.float() * 8.0 - 0.03
        self.t += 1
        done = (self.saved > 0) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"saved": (self.saved > 0)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
