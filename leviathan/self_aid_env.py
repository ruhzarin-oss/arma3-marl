#!/usr/bin/env python3
"""self_aid_env.py — BRIQUE SOIN DE SOI : se soigner quand le SAIGNEMENT devient dangereux, sans lâcher la
position. Combattre garde l'ennemi cloué (il n'avance pas) mais expose (risque de blessure → saignement
qui s'accumule → mort si >1). Se soigner stoppe le saignement MAIS l'ennemi avance (percée). Il faut
ÉQUILIBRER selon le saignement (caché à l'aveugle). A/B : voyant gère ; aveugle se vide (combat tjrs) ou
laisse percer (soigne tjrs). Action : 0 = combattre, 1 = couvert+soin. Métrique = `ok` (survécu ET tenu)."""
import torch


class SelfAidEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 45; self.BREACH = 4.0
        self.obs_dim = 3
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("bleed", "breach", "alive", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.bleed[idx] = 0.0; self.breach[idx] = 0.0; self.alive[idx] = 1.0; self.t[idx] = 0

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            self.bleed if not self.blind else z,                       # mon saignement (le secret)
            (self.breach / self.BREACH).clamp(0, 1), self.alive,
        ], dim=1)

    def step(self, action):
        dev = self.dev
        fight = (action == 0).float() * self.alive
        heal = (action == 1).float() * self.alive
        # combattre : tient l'ennemi (pas de percée) mais expose -> risque de blessure (saignement+)
        wounded = fight * (torch.rand(self.N, device=dev) < 0.22).float()
        self.bleed = (self.bleed + wounded * 0.25 + self.bleed * 0.06 * (self.bleed > 0).float()).clamp(0, 1.5)
        # soigner : stoppe le saignement, mais l'ennemi avance
        self.bleed = (self.bleed - heal * 0.4).clamp(min=0)
        self.breach = self.breach + heal * 0.5                         # soigner = l'ennemi gagne du terrain
        death = (self.bleed >= 1.0).float() * self.alive
        self.alive = self.alive * (1 - death)
        r = self.alive * (self.breach < self.BREACH).float() * 0.12 - death * 6.0 - heal * 0.15 - 0.02   # + rester vivant ET tenir
        self.t += 1
        done = (self.alive == 0) | (self.breach > self.BREACH) | (self.t >= self.max_steps)
        ok = (self.alive > 0) & (self.breach < self.BREACH)            # survécu ET position tenue
        info = {"ok": ok}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
