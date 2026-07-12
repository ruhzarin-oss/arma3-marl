#!/usr/bin/env python3
"""ratissage_env.py — BRIQUE RATISSAGE : balayer une zone SYSTÉMATIQUEMENT pour trouver les ennemis cachés,
sans laisser de trou (ne pas re-fouiller les cases déjà faites). 8 secteurs, certains cachent un ennemi ;
fouiller un secteur = le trouver. PRIME à couvrir des secteurs NEUFS. A/B : voyant voit ce qu'il a déjà
fouillé ; aveugle re-fouille / laisse des trous. Action : fouiller le secteur k (0-7). Métrique = `found`."""
import torch


class RatissageEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 8; self.max_steps = 12
        self.obs_dim = self.D + 1                                       # secteurs déjà fouillés[D] + progression
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        if not hasattr(self, "swept"):
            self.swept = torch.zeros(self.N, self.D, device=dev)
            self.enemy = torch.zeros(self.N, self.D, device=dev)
            self.found = torch.zeros(self.N, device=dev); self.tot = torch.zeros(self.N, device=dev)
            self.t = torch.zeros(self.N, device=dev)
        self.swept[idx] = 0.0
        self.enemy[idx] = (torch.rand(n, self.D, device=dev) < 0.4).float()
        self.found[idx] = 0.0; self.tot[idx] = self.enemy[idx].sum(1); self.t[idx] = 0

    def _obs(self):
        sw = self.swept if not self.blind else torch.zeros(self.N, self.D, device=self.dev)
        return torch.cat([sw, (self.t / self.max_steps).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev; a = action.clamp(0, self.D - 1).unsqueeze(1)
        already = self.swept.gather(1, a).squeeze(1)
        fresh = 1 - already                                            # secteur NEUF ?
        e = self.enemy.gather(1, a).squeeze(1)
        found_now = fresh * e                                          # ennemi trouvé dans un secteur neuf
        self.found = self.found + found_now
        self.swept.scatter_(1, a, torch.ones_like(already).unsqueeze(1))
        r = found_now * 3.0 + fresh * 0.3 - already * 0.5 - 0.04        # prime au secteur NEUF, coût à re-fouiller
        self.t += 1
        done = (self.swept.sum(1) >= self.D) | (self.t >= self.max_steps)
        info = {"found": (self.found / self.tot.clamp(min=1)).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
