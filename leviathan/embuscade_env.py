#!/usr/bin/env python3
"""embuscade_env.py — BRIQUE EMBUSCADE : TENIR LE FEU jusqu'à ce que le MAXIMUM d'ennemis soit dans la
kill-zone, puis DÉCLENCHER (effet max). La colonne traverse la zone : le nombre dedans monte puis redescend.
Déclencher au PIC = tout faucher ; trop tôt/tard = peu. PRIME à déclencher au pic. A/B : voyant voit le
remplissage de la kill-zone ; aveugle déclenche au pif. Action : 0 = tenir le feu, 1 = déclencher (1 fois).
Métrique = `caught` (fraction de la colonne fauchée)."""
import torch


class EmbuscadeEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 24; self.W = 5.0
        self.obs_dim = 3
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("tpeak", "sprung", "caught", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.tpeak[idx] = 6 + torch.rand(n, device=dev) * 12           # pic de remplissage à un instant aléatoire
        self.sprung[idx] = 0.0; self.caught[idx] = 0.0; self.t[idx] = 0

    def _inzone(self):
        return (1 - (self.t - self.tpeak).abs() / self.W).clamp(0, 1)  # triangle : 0 -> pic -> 0

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([
            self._inzone() if not self.blind else z,                   # remplissage de la kill-zone (le secret)
            self.sprung, (self.t / self.max_steps),
        ], dim=1)

    def step(self, action):
        dev = self.dev
        inzone = self._inzone()
        spring = (action == 1).float() * (1 - self.sprung)             # déclenche UNE fois
        catch = spring * inzone                                        # fauche ce qui est DANS la zone à cet instant
        self.caught = self.caught + catch
        prime = spring * (inzone > 0.7).float()                        # déclencher au PIC
        self.sprung = (self.sprung + spring).clamp(0, 1)
        r = catch * 10.0 + prime * 2.0 - spring * (1 - inzone) * 1.0 - 0.04   # déclencher zone vide = révélé pour rien
        self.t += 1
        done = (self.sprung > 0) | (self.t >= self.max_steps)
        info = {"caught": self.caught.clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
