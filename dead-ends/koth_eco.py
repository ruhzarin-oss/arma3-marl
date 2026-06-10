"""KothEco — koth_gpu + ECONOMIE decisive. Revenu/pas ∝ controle de la colline. Choix eco/faction (horloge lente) :
0 garder | 1 renforts (ressusciter l'unite la plus abimee si morte, cout R_COST) | 2 investir_eco (+E_GAIN au taux
de revenu, cout E_COST, paie plus tard). Cree l'arbitrage MAINTENANT-vs-PLUS-TARD + eco-vs-armee + interaction coalition.
Expose money (C,N) et income_rate (C,N)."""
import torch
from koth_gpu import KothGPU


class KothEco(KothGPU):
    R_COST = 22.0; E_COST = 8.0; E_GAIN = 1.0; INCOME = 1.0; CTRL_BONUS = 2.0

    def __init__(self, *a, **kw):
        kw.setdefault("attrition_win", False); kw.setdefault("timeout_decisive", True)
        super().__init__(*a, **kw)
        
        self.cash = torch.zeros(self.C, self.N, device=self.dev); self.income_rate = torch.ones(self.C, self.N, device=self.dev)

    def _reset_rows(self, idx):
        super()._reset_rows(idx)
        if hasattr(self, "income_rate") and idx.numel() > 0:
            self.cash[:, idx] = 0.0; self.income_rate[:, idx] = 1.0

    def eco_step(self, eco_acts):
        d = self.dev; rows = torch.arange(self.N, device=d)
        for c in range(self.C):
            a = eco_acts[c]
            worst = self.dmg[c].argmax(1)
            do_r = (a == 1) & (self.cash[c] >= self.R_COST) & (self.dmg[c][rows, worst] >= self.dmg_dead)
            self.dmg[c][rows[do_r], worst[do_r]] = 0.0
            self.cash[c] = self.cash[c] - self.R_COST * do_r.float()
            do_e = (a == 2) & (self.cash[c] >= self.E_COST)
            self.income_rate[c] = self.income_rate[c] + self.E_GAIN * do_e.float()
            self.cash[c] = self.cash[c] - self.E_COST * do_e.float()

    def in_hill(self, c):
        d2 = (self.px[c] - self.ox[:, None]) ** 2 + (self.py[c] - self.oy[:, None]) ** 2
        return ((d2 <= self.secure_r ** 2) & self._alive(c)).sum(1).float()

    def step(self, acts):
        out = super().step(acts)
        for c in range(self.C):
            self.cash[c] = self.cash[c] + self.INCOME * self.income_rate[c] * (1.0 + self.CTRL_BONUS * (self.in_hill(c) > 0).float())
        return out
