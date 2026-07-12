"""leviathan_env2.py — ETAGE 2 : la menace n'est plus aleatoire, c'est un PAYS ENNEMI (politique FIXEE).

Sous-classe de LeviathanEnv : on ne change QUE la generation de la menace (_roll_threat).
L'ennemi a un POOL DE FORCE qui regenere ; chaque tick il CONCENTRE sa force sur un secteur cible
(Schwerpunkt) et le martele pendant focus_ticks, puis se redeporte sur le secteur tenu le plus faible.
-> la menace devient CORRELEE et PERSISTANTE (massue), plus du bruit i.i.d.
Notre faction (politique apprise) doit LIRE ou l'ennemi masse (menace anticipee) et y concentrer sa reserve,
sans lacher sa caserne/son depot. La difficulte est pilotee par threat_rate (intensite de l'assaut).
Tout le reste (logistique, action TENIR/RENFORCER/DEGARNIR, reward prosperer) est herite tel quel.
"""
import torch
from leviathan_env import LeviathanEnv


class LeviathanEnv2(LeviathanEnv):
    def __init__(self, *a, enemy_regen=3.0, enemy_cap=40.0, focus_ticks=4, **k):
        self.e_regen = enemy_regen; self.e_cap = enemy_cap; self.focus_ticks = focus_ticks
        super().__init__(*a, **k)

    def _ensure_enemy(self):
        if not hasattr(self, "e_force"):
            N, dv = self.N, self.dev
            self.e_force = torch.full((N,), 30.0, device=dv)
            self.e_target = torch.zeros(N, dtype=torch.long, device=dv)
            self.e_timer = torch.zeros(N, dtype=torch.long, device=dv)

    def reset(self, idx=None):
        self._ensure_enemy()
        if idx is None:
            idx = torch.arange(self.N, device=self.dev)
        self.e_force[idx] = 30.0; self.e_timer[idx] = 0
        self.e_target[idx] = int(self.garr0.argmin().item())   # cible initiale = secteur le plus faible
        return super().reset(idx)

    def _roll_threat(self, idx=None):
        self._ensure_enemy()
        rows = torch.arange(self.N, device=self.dev) if idx is None else idx
        n = rows.numel()
        # 1) re-cible si le minuteur est ecoule OU si la cible est tombee : secteur tenu le plus faible
        garr = self.garr[rows].clone(); held = self.owner[rows] > 0
        garr = torch.where(held, garr, torch.full_like(garr, 1e9))
        tgt_held = held.gather(1, self.e_target[rows].unsqueeze(1)).squeeze(1)
        retarget = (self.e_timer[rows] <= 0) | (~tgt_held)
        self.e_target[rows] = torch.where(retarget, garr.argmin(1), self.e_target[rows])
        self.e_timer[rows] = torch.where(retarget, torch.full_like(self.e_timer[rows], self.focus_ticks), self.e_timer[rows] - 1)
        # 2) PRESSION concentree SOUTENUE sur la cible (le Schwerpunkt qui ne lache pas ; intensite ~ threat_rate)
        intensity = 10.0 * self.threat_rate
        thr = torch.zeros(n, self.K, device=self.dev)
        thr.scatter_(1, self.e_target[rows].unsqueeze(1), torch.full((n, 1), intensity, device=self.dev))
        # 4) sondage leger sur les autres secteurs tenus (fixe l'ennemi diffus)
        probe = (torch.rand(n, self.K, device=self.dev) < 0.25 * self.threat_rate) & held
        thr = thr + probe.float() * torch.rand(n, self.K, device=self.dev) * 2.0
        # 5) menace = decroissance + nouvelle (visible le tick suivant -> anticipation conservee)
        self.threat[rows] = self.threat[rows] * 0.4 + thr * held.float()
