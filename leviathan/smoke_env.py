#!/usr/bin/env python3
"""smoke_env.py — BRIQUE FUMIGÈNE : déployer la fumée pour TRAVERSER une zone à découvert létale. Traverser
à nu = mort ; sous fumée = sûr. PRIME À L'USAGE = déployer la fumée AVANT d'entrer dans la zone. A/B :
voyant voit la zone de danger et fume au bon moment ; aveugle traverse à découvert → meurt.
Action : 0 = avancer, 1 = déployer fumée. Métrique = `reached`."""
import torch


class SmokeEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 30
        self.obs_dim = 4
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("prog", "smoke", "active", "alive", "t", "reached"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.prog[idx] = 0.0; self.smoke[idx] = 1.0; self.active[idx] = 0.0
        self.alive[idx] = 1.0; self.t[idx] = 0; self.reached[idx] = 0.0

    def _in_danger(self):
        return ((self.prog > 0.4) & (self.prog < 0.72)).float()

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            self.prog,
            self._in_danger() if not self.blind else z,               # la zone létale (le secret)
            (self.active > 0).float(), self.smoke,
        ], dim=1)

    def step(self, action):
        dev = self.dev
        deploy = (action == 1).float() * (self.smoke > 0).float() * self.alive
        before = self.prog.clone()
        # déployer la fumée juste avant la zone = la PRIME
        prime = deploy * ((self.prog > 0.28) & (self.prog < 0.42)).float()
        self.active = torch.where(deploy > 0, torch.full_like(self.active, 5.0), (self.active - 1).clamp(min=0))
        self.smoke = (self.smoke - deploy).clamp(min=0)
        advance = (action == 0).float() * self.alive
        ind = self._in_danger()
        can_cross = ((1 - ind) + ind * (self.active > 0).float()).clamp(0, 1)   # dans le danger : avance SEULEMENT sous fumée
        self.prog = (self.prog + advance * 0.1 * can_cross).clamp(0, 1.2)
        self.reached = ((self.prog >= 1.0) & (self.alive > 0)).float()
        r = (self.prog - before) * 0.5 + self.reached * 10.0 + prime * 2.0 - 0.03
        self.t += 1
        done = (self.reached > 0) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"reached": (self.reached > 0)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
