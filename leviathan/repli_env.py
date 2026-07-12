#!/usr/bin/env python3
"""repli_env.py — BRIQUE REPLI : décrocher AU BON MOMENT. Combattre tant que la menace est gérable
(accumuler des neutralisations), se replier AVANT que la menace ne devienne mortelle. A/B : voyant (sent
la submersion qui monte) time son repli ; aveugle se replie trop tôt (peu de kills) ou trop tard (mort).
Action : 0 = combattre, 1 = se replier (au couvert = sûr). Métrique = `score` (kills si survécu, sinon 0)."""
import torch


class RepliEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 30; self.MAXK = 12.0
        self.obs_dim = 3
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("threat", "retreated", "alive", "kills", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.threat[idx] = torch.rand(n, device=dev) * 0.15            # submersion initiale faible
        self.retreated[idx] = 0.0; self.alive[idx] = 1.0; self.kills[idx] = 0.0; self.t[idx] = 0

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            self.threat if not self.blind else z,                      # la submersion qui monte (le secret)
            self.retreated, (self.kills / self.MAXK).clamp(0, 1),
        ], dim=1)

    def step(self, action):
        dev = self.dev
        fight = (action == 0).float() * self.alive * (1 - self.retreated)
        retreat = (action == 1).float()
        self.retreated = torch.clamp(self.retreated + retreat, 0, 1)   # une fois replié -> au couvert (sûr)
        kill = fight
        death = fight * (torch.rand(self.N, device=dev) < self.threat * 0.11).float()
        self.alive = self.alive * (1 - death)
        self.kills = self.kills + kill * self.alive
        self.threat = (self.threat + 0.05).clamp(0, 1.2)               # la menace monte inexorablement
        r = kill * 1.0 - death * 6.0 - 0.02
        self.t += 1
        # fin : mort, timeout, ou replié depuis 2 pas (extrait)
        done = (self.alive == 0) | (self.t >= self.max_steps)          # le repli ne FINIT plus l'épisode (juste : sûr)
        score = torch.where(self.alive > 0, (self.kills / self.MAXK).clamp(0, 1), torch.zeros_like(self.kills))
        r = r + done.float() * score * 6.0                             # récompense TERMINALE = le score (kills si survécu)
        info = {"score": score}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
