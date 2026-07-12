#!/usr/bin/env python3
"""nuit_env.py — BRIQUE NUIT/NVG : exploiter la fenêtre où TOI (NVG) tu vois et l'ennemi NON. Engager de
NUIT = kill sûr (avantage) ; engager de JOUR = exposé, il riposte. Cycle jour/nuit. PRIME à engager pendant
l'avantage nocturne. A/B : voyant voit qu'il fait nuit ; aveugle engage au pif → se fait toucher de jour.
Action : 0 = tenir, 1 = engager. Métrique = `score` (kills si survécu)."""
import torch


class NuitEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 45; self.MAXK = 14.0
        self.obs_dim = 4
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("night", "kills", "alive", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.night[idx] = (torch.rand(n, device=dev) < 0.5).float()
        self.kills[idx] = 0.0; self.alive[idx] = 1.0; self.t[idx] = 0

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            self.night if not self.blind else z,                       # fait-il nuit (le secret = l'avantage)
            (self.kills / self.MAXK).clamp(0, 1), self.alive,
            torch.ones(self.N, device=self.dev),                       # ennemi présent
        ], dim=1)

    def step(self, action):
        dev = self.dev
        engage = (action == 1).float() * self.alive
        kill = engage                                                  # toucher l'ennemi
        prime = engage * self.night                                    # frapper pendant l'avantage NVG = décisif
        day_exposed = engage * (1 - self.night)                        # engager de jour = exposé
        hit = (torch.rand(self.N, device=dev) < day_exposed * 0.32).float()
        self.alive = self.alive * (1 - hit)
        self.kills = self.kills + kill * self.alive
        r = kill * 1.0 + prime * 1.0 - hit * 4.0 - 0.03
        flip = (torch.rand(self.N, device=dev) < 0.07).float()         # le cycle jour/nuit tourne
        self.night = torch.where(flip > 0, 1 - self.night, self.night)
        self.t += 1
        done = (self.alive == 0) | (self.t >= self.max_steps)
        score = torch.where(self.alive > 0, (self.kills / self.MAXK).clamp(0, 1), torch.zeros_like(self.kills))
        info = {"score": score}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
