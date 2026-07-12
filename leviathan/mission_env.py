#!/usr/bin/env python3
"""mission_env.py — BRIQUE ORCHESTRATION : utiliser le BON OUTIL de l'arsenal selon la situation, pour
accomplir la mission. 5 types de situation → 5 outils :
  0 EXPOSÉ→tir visé · 1 COUVERT→grenade · 2 RETRANCHÉ→flanc · 3 À DÉCOUVERT→fumigène · 4 CLOUÉ→suppression.
Grenades/fumis LIMITÉS (pas de gaspillage). Bon outil dispo = situation franchie + PRIME à l'usage ;
mauvais outil = bloqué + coût (et riposte si la situation est dangereuse). A/B : voyant lit la situation et
sort le bon outil ; aveugle devine, gaspille, se fait toucher. Métrique = `cleared` (mission accomplie)."""
import torch


class MissionEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.K = 6; self.T = 2; self.max_steps = 22
        self.obs_dim = 5 + 3                                            # type[5] + grenades + fumis + progression
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("ctype", "grenades", "smoke", "cleared", "t", "alive"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.ctype[idx] = torch.randint(0, 5, (n,), device=dev).float()
        self.grenades[idx] = float(self.T); self.smoke[idx] = float(self.T)
        self.cleared[idx] = 0.0; self.t[idx] = 0; self.alive[idx] = 1.0

    def _obs(self):
        oh = torch.zeros(self.N, 5, device=self.dev)
        if not self.blind: oh.scatter_(1, self.ctype.long().unsqueeze(1), 1.0)   # le TYPE de situation = le secret
        return torch.cat([oh, (self.grenades / self.T).unsqueeze(1),
                          (self.smoke / self.T).unsqueeze(1), (self.cleared / self.K).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev; ct = self.ctype.long()
        correct = (action == ct).float()
        is_gren = (action == 1).float(); is_smoke = (action == 3).float()
        avail = (1 - is_gren * (self.grenades <= 0).float() - is_smoke * (self.smoke <= 0).float()).clamp(0, 1)
        effective = correct * avail * self.alive
        self.grenades = (self.grenades - is_gren).clamp(min=0)         # consommé même si mal employé (gaspillage)
        self.smoke = (self.smoke - is_smoke).clamp(min=0)
        self.cleared = self.cleared + effective
        dangerous = ((ct == 2) | (ct == 4)).float(); wrong = 1 - correct
        hit = wrong * dangerous * (torch.rand(self.N, device=dev) < 0.25).float()
        self.alive = self.alive * (1 - hit)
        r = (effective * 3.0 + effective * 1.0                          # franchir + PRIME À L'USAGE
             - wrong * 0.3 - is_gren * (1 - correct) * 1.0 - is_smoke * (1 - correct) * 1.0   # gaspiller un consommable
             - hit * 4.0 - 0.05)
        newt = torch.randint(0, 5, (self.N,), device=dev).float()
        self.ctype = torch.where(effective > 0, newt, self.ctype)      # situation suivante quand franchie
        self.t += 1
        done = (self.cleared >= self.K) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"cleared": (self.cleared / self.K).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
