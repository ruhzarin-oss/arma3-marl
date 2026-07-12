#!/usr/bin/env python3
"""soutien_env.py — BRIQUE SOUTIEN MUTUEL : couvrir l'ANGLE MORT d'un coéquipier. L'ami a un secteur
aveugle qui CHANGE ; quand il est exposé et qu'un ennemi est dans son angle mort, il faut TIRER ce secteur
pour le couvrir, sinon il tombe. A/B : voyant (voit l'angle mort de l'ami) couvre ; aveugle tire au pif.
Métrique = `ally_survived` (l'ami a tenu l'épisode)."""
import torch


class SoutienEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 8; self.max_steps = 40
        self.obs_dim = self.D + self.D + 1                              # ennemis[D] + angle-mort-ami[D] + ami-exposé
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("ally_alive", "t", "blindsec", "exposed"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        if not hasattr(self, "enemies"): self.enemies = torch.zeros(self.N, self.D, device=dev)
        self.ally_alive[idx] = 1.0; self.t[idx] = 0
        self.enemies[idx] = (torch.rand(n, self.D, device=dev) < 0.3).float()
        self.blindsec[idx] = torch.randint(0, self.D, (n,), device=dev).float()
        self.exposed[idx] = (torch.rand(n, device=dev) < 0.4).float()

    def _obs(self):
        bonehot = torch.zeros(self.N, self.D, device=self.dev)
        bonehot.scatter_(1, self.blindsec.long().unsqueeze(1), 1.0)
        if self.blind:
            bonehot = bonehot * 0.0; exp = torch.zeros(self.N, device=self.dev)
        else:
            exp = self.exposed
        return torch.cat([self.enemies, bonehot, exp.unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev; bs = self.blindsec.long().unsqueeze(1)
        enemy_in_blind = self.enemies.gather(1, bs).squeeze(1)
        covering = (action == self.blindsec.long()).float()
        # menace sur l'ami : exposé + ennemi dans son angle mort + je ne couvre PAS -> il peut tomber
        threat = self.exposed * enemy_in_blind * (1 - covering)
        hit = (torch.rand(self.N, device=dev) < threat * 0.7)
        self.ally_alive = self.ally_alive * (~hit).float()
        # si je couvre le bon secteur avec un ennemi -> je le neutralise
        good = covering * enemy_in_blind
        self.enemies.scatter_(1, bs, self.enemies.gather(1, bs) * (1 - good).unsqueeze(1))
        r = good * 0.5 - hit.float() * 5.0 + self.ally_alive * 0.05 - 0.02
        # évolution : nouvel angle mort + ennemis qui bougent
        self.blindsec = torch.randint(0, self.D, (self.N,), device=dev).float()
        self.exposed = (torch.rand(self.N, device=dev) < 0.4).float()
        churn = (torch.rand(self.N, self.D, device=dev) < 0.15)
        self.enemies = torch.where(churn, (torch.rand(self.N, self.D, device=dev) < 0.3).float(), self.enemies)
        self.t += 1
        done = (self.ally_alive == 0) | (self.t >= self.max_steps)
        info = {"ally_survived": (self.ally_alive > 0)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
