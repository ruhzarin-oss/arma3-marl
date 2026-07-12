#!/usr/bin/env python3
"""marksman_env.py — BRIQUE MARKSMAN : choisir les cibles PRIORITAIRES (HVT : officier/MG, valeur ×3)
parmi plusieurs, en peu de tirs. Les HVT non-tués font des dégâts (l'équipe souffre). A/B : voyant (voit
qui est HVT) descend les HVT d'abord ; aveugle tire au pif. Action = engager la cible k (nact=K).
Métrique = `hvt_down` (fraction de HVT neutralisés)."""
import torch


class MarksmanEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.K = 5; self.max_steps = 6
        self.obs_dim = self.K * 2                                       # par cible : présente + est_HVT
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        if not hasattr(self, "present"):
            self.present = torch.zeros(self.N, self.K, device=dev)
            self.hvt = torch.zeros(self.N, self.K, device=dev)
            self.t = torch.zeros(self.N, device=dev); self.hvt0 = torch.zeros(self.N, device=dev)
            self.hvtdown = torch.zeros(self.N, device=dev)
        self.present[idx] = 1.0
        self.hvt[idx] = (torch.rand(n, self.K, device=dev) < 0.4).float()   # ~2 HVT sur 5
        self.t[idx] = 0; self.hvt0[idx] = self.hvt[idx].sum(1); self.hvtdown[idx] = 0.0

    def _obs(self):
        h = self.hvt if not self.blind else torch.zeros(self.N, self.K, device=self.dev)
        return torch.cat([self.present, h], dim=1)

    def step(self, action):
        dev = self.dev
        a = action.clamp(0, self.K - 1).unsqueeze(1)
        hit_present = self.present.gather(1, a).squeeze(1)
        hit_hvt = self.hvt.gather(1, a).squeeze(1) * hit_present
        # neutralise la cible visée (si présente)
        self.present.scatter_(1, a, self.present.gather(1, a) * 0.0)
        self.hvt.scatter_(1, a, self.hvt.gather(1, a) * 0.0)
        self.hvtdown = self.hvtdown + hit_hvt
        r = hit_hvt * 3.0 + (hit_present - hit_hvt) * 1.0 - 0.05        # HVT vaut ×3
        self.t += 1
        done = (self.t >= self.max_steps) | (self.present.sum(1) == 0)
        frac = self.hvtdown / self.hvt0.clamp(min=1)
        info = {"hvt_down": frac}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
