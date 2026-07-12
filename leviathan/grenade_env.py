#!/usr/bin/env python3
"""grenade_env.py — BRIQUE GRENADE : neutraliser 4 ennemis avec 2 grenades + le tir visé. Un ennemi EN
COUVERT DUR ne tombe QUE à la grenade (tir visé inutile) ; un ennemi EXPOSÉ tombe au tir visé. Grenades
RARES → il faut les RÉSERVER aux ennemis en couvert (et viser les exposés). A/B : voyant (voit le couvert)
économise ; aveugle gaspille les grenades / tire dans le vide. Métrique = `cleared` (fraction neutralisée)."""
import torch


class GrenadeEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 24
        self.NT = 4; self.G = 2; self.obs_dim = 5
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("in_cover", "grenades", "neut", "t", "alive"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.in_cover[idx] = (torch.rand(n, device=dev) < 0.5).float()
        self.grenades[idx] = float(self.G); self.neut[idx] = 0; self.t[idx] = 0; self.alive[idx] = 1.0

    def _obs(self):
        ic = self.in_cover if not self.blind else torch.zeros(self.N, device=self.dev)
        present = (self.neut < self.NT).float()
        return torch.stack([ic, self.grenades / self.G, self.neut / self.NT, present,
                            (self.t / self.max_steps)], dim=1)

    def step(self, action):
        dev = self.dev
        present = (self.neut < self.NT).float()
        aimed = (action == 1).float() * present
        gren = (action == 2).float() * present * (self.grenades > 0).float()
        kill = ((aimed * (1 - self.in_cover)) + gren).clamp(0, 1)       # visé si exposé, grenade toujours
        wasted = gren * (1 - self.in_cover)                            # grenade sur exposé = gaspillage
        prime = gren * self.in_cover * kill                           # PRIME À L'USAGE : grenade sur ennemi EN COUVERT = décisif
        probe = aimed * self.in_cover                                 # viser un couvert = sonder à l'aveugle (perdu + exposé)
        self.grenades = (self.grenades - gren).clamp(min=0)
        self.neut = self.neut + kill
        new_ic = (torch.rand(self.N, device=dev) < 0.5).float()
        self.in_cover = torch.where(kill > 0, new_ic, self.in_cover)   # ennemi suivant quand on en tue un
        dead = probe * (torch.rand(self.N, device=dev) < 0.3).float()  # SONDER un couvert (viser à l'aveugle) = riposte
        self.alive = self.alive * (1 - dead)
        r = kill * 3.0 + prime * 2.0 - wasted * 0.5 - probe * 0.5 - dead * 4.0 - 0.05
        self.t += 1
        timeout = (self.t >= self.max_steps) & (self.neut < self.NT)   # rester avec des couverts vivants = coûteux
        r = r - timeout.float() * 3.0
        frac = self.neut / self.NT
        done = (self.neut >= self.NT) | (self.t >= self.max_steps) | (self.alive == 0)
        info = {"cleared": frac}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
