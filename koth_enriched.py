"""KothEnriched — koth_gpu + DILEMME : une faction affaiblie ALEATOIREMENT par episode (unites tuees au spawn).
La bonne posture depend de QUI est faible (presser l'ennemi faible / defendre si c'est toi) -> richesse decisionnelle
qu'une regle 'par rang' ne capture pas. Expose self.weak_faction (N,) = camp faible (-1 si aucun)."""
import math, torch
from koth_gpu import KothGPU


class KothEnriched(KothGPU):
    def __init__(self, *a, weak_p=0.7, weak_kill=0.5, **kw):
        kw.setdefault("attrition_win", False); kw.setdefault("timeout_decisive", True)
        super().__init__(*a, **kw)
        self.weak_p = weak_p; self.weak_kill = weak_kill
        self.weak_faction = torch.full((self.N,), -1, dtype=torch.long, device=self.dev)
        self._reset_rows(torch.arange(self.N, device=self.dev))

    def _reset_rows(self, idx):
        super()._reset_rows(idx)
        if getattr(self, "weak_p", 0.0) <= 0.0 or idx.numel() == 0:
            return
        n = idx.numel(); A, C, d = self.A, self.C, self.dev
        hit = torch.rand(n, generator=self.g, device=d) < self.weak_p
        w = torch.randint(0, C, (n,), generator=self.g, device=d)
        self.weak_faction[idx] = torch.where(hit, w, torch.full_like(w, -1))
        nkill = max(1, int(round(A * self.weak_kill)))
        kcols = torch.arange(nkill, device=d).unsqueeze(0)
        for c in range(C):
            m = hit & (w == c)
            if m.any():
                rows = idx[m]
                self.dmg[c][rows.unsqueeze(1), kcols] = 1.0
        for c in range(C):
            px = self.px[c, idx]; py = self.py[c, idx]; al = (self.dmg[c, idx] < self.dmg_dead).float()
            dd = torch.sqrt((px - self.ox[idx, None]) ** 2 + (py - self.oy[idx, None]) ** 2) / self.scale
            den = al.sum(1); self.prev_d[c, idx] = torch.where(den > 0, (dd * al).sum(1) / den.clamp(min=1), torch.zeros_like(den))
