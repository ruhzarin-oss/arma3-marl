#!/usr/bin/env python3
"""grenadier_env.py — BRIQUE GRENADIER : l'UGL (lance-grenade) fauche les GROUPES (dégât de zone) ; le tir
direct ne tue qu'un homme. UGL limitée → la RÉSERVER aux groupes. PRIME à l'usage UGL sur un groupe ;
sonder (tirer un groupe au fusil) = lent + riposte. Action : 0 couvert, 1 fusil, 2 UGL. A/B : voyant voit
les groupes ; aveugle gaspille l'UGL. Métrique = `cleared` (fraction neutralisée)."""
import torch


class GrenadierEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 24; self.NT = 5; self.G = 2
        self.obs_dim = 5
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("grouped", "ugl", "neut", "t", "alive"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.grouped[idx] = (torch.rand(n, device=dev) < 0.45).float()
        self.ugl[idx] = float(self.G); self.neut[idx] = 0.0; self.t[idx] = 0; self.alive[idx] = 1.0

    def _obs(self):
        g = self.grouped if not self.blind else torch.zeros(self.N, device=self.dev)
        return torch.stack([g, self.ugl / self.G, self.neut / self.NT, (self.neut < self.NT).float(),
                            self.t / self.max_steps], dim=1)

    def step(self, action):
        dev = self.dev; present = (self.neut < self.NT).float()
        rifle = (action == 1).float() * present
        ugl = (action == 2).float() * present * (self.ugl > 0).float()
        kill = ((rifle * (1 - self.grouped)) + ugl * (1 + self.grouped)).clamp(0, 2)   # UGL sur groupe = ×2
        kill = kill * self.alive
        prime = ugl * self.grouped                                     # UGL sur un GROUPE = l'usage décisif
        probe = rifle * self.grouped                                   # fusiller un groupe = sonder (lent, exposé)
        self.ugl = (self.ugl - ugl).clamp(min=0)
        self.neut = (self.neut + kill).clamp(max=self.NT)
        dead = probe * (torch.rand(self.N, device=dev) < 0.25).float()
        self.alive = self.alive * (1 - dead)
        newg = (torch.rand(self.N, device=dev) < 0.45).float()
        self.grouped = torch.where(kill > 0, newg, self.grouped)
        r = kill * 3.0 + prime * 2.0 - ugl * (1 - self.grouped) * 0.6 - probe * 0.4 - dead * 4.0 - 0.05
        self.t += 1
        timeout = (self.t >= self.max_steps) & (self.neut < self.NT)
        r = r - timeout.float() * 3.0
        done = (self.neut >= self.NT) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"cleared": (self.neut / self.NT).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
