#!/usr/bin/env python3
"""mines_env.py — BRIQUE MINES : poser les mines sur l'AXE D'APPROCHE de l'ennemi pour les piéger. Mine sur
le bon axe = les ennemis sautent dessus ; mauvais axe = gaspillée. Mines limitées. PRIME à poser sur l'axe
réel. A/B : voyant voit d'où vient l'ennemi ; aveugle pose au pif. Action : poser dans le secteur k (0-7),
ou attendre (8). Métrique = `caught` (fraction des vagues piégées)."""
import torch


class MinesEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 8; self.max_steps = 20; self.MINES = 3; self.WAVES = 4
        self.obs_dim = self.D + 2                                       # axe d'approche[D] + mines + vagues
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("axis", "mines", "caught", "wave", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.axis[idx] = torch.randint(0, self.D, (n,), device=dev).float()
        self.mines[idx] = float(self.MINES); self.caught[idx] = 0.0; self.wave[idx] = 0.0; self.t[idx] = 0

    def _obs(self):
        oh = torch.zeros(self.N, self.D, device=self.dev)
        if not self.blind: oh.scatter_(1, self.axis.long().unsqueeze(1), 1.0)   # l'axe d'approche = le secret
        return torch.cat([oh, (self.mines / self.MINES).unsqueeze(1), (self.wave / self.WAVES).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev
        place = (action < self.D).float() * (self.mines > 0).float()
        on_axis = (action == self.axis.long()).float() * place
        catch = on_axis                                                # mine sur l'axe réel -> piège la vague
        self.caught = self.caught + catch
        self.mines = (self.mines - place).clamp(min=0)
        prime = on_axis                                                # poser sur le bon axe = l'usage
        wasted = place * (1 - on_axis)                                 # mine sur un mauvais axe = perdue
        r = catch * 4.0 + prime * 1.0 - wasted * 1.0 - 0.05
        # vague suivante : nouvel axe d'approche
        self.wave = self.wave + place                                  # chaque pose = on traite une vague
        newax = torch.randint(0, self.D, (self.N,), device=dev).float()
        self.axis = torch.where(place > 0, newax, self.axis)
        self.t += 1
        done = (self.wave >= self.WAVES) | (self.mines <= 0) | (self.t >= self.max_steps)
        info = {"caught": (self.caught / self.WAVES).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
