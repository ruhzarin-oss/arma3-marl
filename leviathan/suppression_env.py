#!/usr/bin/env python3
"""suppression_env.py — BRIQUE SUPPRESSION : un soldat (base de feu) doit CLOUER un ennemi pendant qu'un
AMI manœuvre à découvert. Le skill = supprimer AU BON MOMENT (quand l'ami est exposé) → l'ami avance en
sécurité. Supprimer ≠ tuer : ça réduit l'efficacité de l'ennemi le temps de la manœuvre.

A/B : voyant (voit l'expo de l'ami + le niveau de suppression) vs aveugle (tire à l'aveugle, mal timé)."""
import torch


class SuppressionEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 40
        self.obs_dim = 8
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("edist", "esupp", "ealive", "fprog", "falive", "t", "mycover", "ammo"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.edist[idx] = 100 + torch.rand(n, device=dev) * 50          # ennemi à 100-150 m
        self.esupp[idx] = 0.0                                            # niveau de suppression (0-1)
        self.ealive[idx] = 1.0
        self.ammo[idx] = 10 + torch.rand(n, device=dev) * 4             # budget suppression SERRÉ (10-14) -> faut timer
        self.fprog[idx] = 0.0                                            # progression de l'ami (0->1 = atteint le flanc)
        self.falive[idx] = 1.0
        self.t[idx] = 0; self.mycover[idx] = (torch.rand(n, device=dev) > 0.5).float()

    def _fexposed(self):
        # l'ami est EXPOSÉ pendant la traversée à découvert (milieu de la manœuvre)
        return ((self.fprog > 0.15) & (self.fprog < 0.85)).float()

    def _obs(self):
        exposed = self._fexposed()
        o = torch.stack([
            (self.edist / 150.0).clamp(0, 1),                           # distance ennemi
            self.ealive,                                                # ennemi vivant
            self.esupp if not self.blind else torch.zeros_like(self.esupp),     # suis-je en train de le clouer
            self.fprog if not self.blind else torch.zeros_like(self.fprog),     # où en est l'ami
            exposed if not self.blind else torch.zeros_like(exposed),           # l'ami est-il exposé MAINTENANT (le signal clé)
            self.falive,                                                # ami vivant
            self.mycover,                                               # suis-je à couvert
            (self.ammo / 14.0).clamp(0, 1),                             # mon budget suppression restant (proprioception)
        ], dim=1)
        return o

    def step(self, mode):
        # mode : 0 = couvert (ne tire pas, se protège) | 1 = tir visé (peut tuer, expose) | 2 = SUPPRESSION (cloue, expose)
        dev = self.dev
        suppress = (mode == 2).float(); aimed = (mode == 1).float(); cover = (mode == 0).float()
        exposed_f = self._fexposed()
        # suppression effective SEULEMENT si munitions (budget serré -> faut la RÉSERVER pour la traversée)
        sup_eff = suppress * (self.ammo > 0).float()
        self.ammo = (self.ammo - sup_eff).clamp(min=0)
        self.esupp = (self.esupp * 0.6 + sup_eff * 0.6).clamp(0, 1)
        pinned = (self.esupp > 0.5).float() * self.ealive               # ennemi cloué ?
        # l'AMI avance LIBREMENT hors zone exposée, mais ne TRAVERSE l'exposé QUE s'il est couvert (cloué/mort)
        covered = (pinned + (1 - self.ealive)).clamp(0, 1)
        can_advance = ((1 - exposed_f) + exposed_f * covered).clamp(0, 1)
        self.fprog = (self.fprog + 0.1 * can_advance).clamp(0, 1.2)
        # exposé + non-cloué + ennemi vivant = TRÈS dangereux (il faut le couvrir)
        danger = exposed_f * (1 - pinned) * self.ealive
        hit_f = (torch.rand(self.N, device=dev) < danger * 0.6)
        self.falive = self.falive * (~hit_f).float()
        # l'ennemi tire sur MOI si je l'expose (tir/suppression) et qu'il n'est pas cloué
        myexpo = (aimed + sup_eff) * (1 - self.mycover) * (1 - self.esupp) * self.ealive
        hit_me = (torch.rand(self.N, device=dev) < myexpo * 0.18)
        # tir visé : petite chance de tuer l'ennemi
        kill_e = (torch.rand(self.N, device=dev) < aimed * 0.12) * self.ealive
        self.ealive = self.ealive * (1 - kill_e.float())
        self.mycover = cover                                            # se couvrir met à couvert au prochain pas

        reached = (self.fprog >= 1.0) & (self.falive > 0)
        r = (pinned * exposed_f) * 0.3                                  # récompense de CLOUER pendant que l'ami est exposé
        r = r + reached.float() * 10.0                                  # l'ami a atteint le flanc = mission
        r = r - (hit_f.float()) * 8.0                                   # ami abattu = échec
        r = r - (hit_me.float()) * 3.0                                  # je me fais toucher
        r = r + kill_e.float() * 1.0                                    # bonus tuer l'ennemi (secondaire)
        r = r - 0.02
        self.t += 1
        dead_me = hit_me
        done = reached | (self.falive == 0) | dead_me | (self.t >= self.max_steps)
        info = {"reached": reached, "fdown": hit_f}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
