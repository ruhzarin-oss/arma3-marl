#!/usr/bin/env python3
"""mg_env.py — BRIQUE MITRAILLEUR/STATIQUE : suppression de ZONE par RAFALES en gérant la SURCHAUFFE
(tir continu → enraye). Tirer le secteur le plus dense, mais cesser pour refroidir. A/B : voyant (voit la
chaleur) tire par rafales ; aveugle tire en continu → enraye → les ennemis percent. Action : 0-7 = tirer
ce secteur, 8 = cesser (refroidir). Métrique = `held` (zone tenue = ennemis arrêtés)."""
import torch


class MgEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 8; self.max_steps = 45
        self.obs_dim = self.D + 2                                       # densité[D] + chaleur + enrayé
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("heat", "jammed", "t", "breached"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        if not hasattr(self, "dens"): self.dens = torch.zeros(self.N, self.D, device=dev)
        self.dens[idx] = (torch.rand(n, self.D, device=dev) < 0.35).float() * torch.rand(n, self.D, device=dev)
        self.heat[idx] = 0.0; self.jammed[idx] = 0.0; self.t[idx] = 0; self.breached[idx] = 0.0

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        return torch.cat([self.dens,
                          (self.heat if not self.blind else z).unsqueeze(1),
                          (self.jammed if not self.blind else z).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev
        cease = (action == 8).float()
        fire = (action < self.D).float() * (1 - self.jammed)           # ne tire pas si enrayé
        a = action.clamp(0, self.D - 1).unsqueeze(1)
        # tir : réduit la densité du secteur visé, chauffe
        killed = fire * self.dens.gather(1, a).squeeze(1)
        self.dens.scatter_(1, a, (self.dens.gather(1, a) - fire.unsqueeze(1) * 0.5).clamp(min=0))
        self.heat = (self.heat + fire * 0.16 - cease * 0.25 - 0.02).clamp(0, 1.3)
        self.jammed = torch.where(self.heat > 1.0, torch.ones_like(self.heat), self.jammed)
        self.jammed = torch.where(self.heat < 0.4, torch.zeros_like(self.heat), self.jammed)   # se désenraye en refroidissant
        # les ennemis non-supprimés avancent -> percée (plus rapide -> faut tirer EFFICACE = gérer la chaleur)
        adv = self.dens.sum(1)
        self.breached = self.breached + adv * 0.07
        churn = (torch.rand(self.N, self.D, device=dev) < 0.12)
        self.dens = torch.where(churn, torch.rand(self.N, self.D, device=dev) * 0.9, self.dens)
        r = killed * 1.5 - self.jammed * 0.4 - adv * 0.06 - 0.02
        self.t += 1
        done = (self.t >= self.max_steps) | (self.breached > 4.0)
        info = {"held": (self.breached < 4.0)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
