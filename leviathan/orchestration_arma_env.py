#!/usr/bin/env python3
"""orchestration_arma_env.py — ORCHESTRATION FUSIONNÉE sur les VRAIES features Arma (pas le one-hot toy).
Le type de situation est LATENT (caché) : la politique doit l'INFÉRER de ~10 signaux Arma-calculables,
bruités et qui se chevauchent (comme en vrai), puis sortir la bonne tactique. Récompense = succès mission
(pas de label). C'est le socle live : perception réelle → tactique. Re-lie l'orchestration (+91 du toy) sur
des features qu'on sait produire dans Arma (coque 12-rayons + LOS + événements-balles + inventaire).

Latent s (0..4) et sa tactique alignée (action==s = correct) :
  0 EXPOSÉ→TIR · 1 COUVERT→GRENADE · 2 RETRANCHÉ→FLANC · 3 À DÉCOUVERT→FUMIGÈNE · 4 CLOUÉ→SUPPRESSION
Features (obs_dim=10, ordre) : [0]dist [1]visible(LOS) [2]ennemi-derrière-couvert [3]ennemi-retranché
  [4]mon-exposition [5]terrain-ouvert [6]feu-entrant [7]grenades/2 [8]fumis/2 [9]alliés-proches.
A/B : AVEUGLE = features [1..6] (les 6 qui révèlent la situation) mises à 0 → doit deviner. Métrique=`cleared`."""
import torch


class OrchestrationArmaEnv:
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.K = 6; self.T = 2; self.max_steps = 24
        self.obs_dim = 10
        torch.manual_seed(seed)
        self._reset(torch.arange(n, device=device))

    def _gen(self, idx):
        """(Re)génère les features de perception pour une NOUVELLE situation latente sur idx."""
        n = idx.numel(); dev = self.dev
        s = torch.randint(0, 5, (n,), device=dev).float()
        self.s[idx] = s
        lo = lambda: torch.rand(n, device=dev) * 0.3                    # bruit de fond bas
        hi = lambda: 0.7 + torch.rand(n, device=dev) * 0.3             # signature haute
        self.dist[idx] = 0.2 + torch.rand(n, device=dev) * 0.7
        behind = torch.where(s == 1, hi(), lo())                       # COUVERT
        entr = torch.where(s == 2, hi(), lo())                         # RETRANCHÉ
        expo = torch.where(s == 3, hi(), lo())                         # À DÉCOUVERT
        openg = torch.where(s == 3, 0.6 + torch.rand(n, device=dev) * 0.4, lo())
        fire = torch.where(s == 4, hi(), lo())                         # CLOUÉ
        vis = torch.where(s == 1, 0.3 + torch.rand(n, device=dev) * 0.4,  # derrière couvert = moins visible
                          0.6 + torch.rand(n, device=dev) * 0.4)
        self.vis[idx] = vis; self.behind[idx] = behind; self.entr[idx] = entr
        self.expo[idx] = expo; self.openg[idx] = openg; self.fire[idx] = fire
        self.allies[idx] = torch.rand(n, device=dev)

    def _reset(self, idx):
        dev = self.dev
        for a in ("s", "dist", "vis", "behind", "entr", "expo", "openg", "fire", "allies",
                  "grenades", "smoke", "cleared", "t", "alive"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.grenades[idx] = float(self.T); self.smoke[idx] = float(self.T)
        self.cleared[idx] = 0.0; self.t[idx] = 0.0; self.alive[idx] = 1.0
        self._gen(idx)

    def _obs(self):
        z = torch.zeros(self.N, device=self.dev)
        b = self.blind
        return torch.stack([
            self.dist,                                                 # [0] dist (gardée)
            z if b else self.vis,                                      # [1] visible
            z if b else self.behind,                                   # [2] ennemi derrière couvert
            z if b else self.entr,                                     # [3] ennemi retranché
            z if b else self.expo,                                     # [4] mon exposition
            z if b else self.openg,                                    # [5] terrain ouvert
            z if b else self.fire,                                     # [6] feu entrant
            self.grenades / self.T,                                    # [7] grenades (gardée)
            self.smoke / self.T,                                       # [8] fumis (gardée)
            self.allies,                                               # [9] alliés proches (gardée)
        ], dim=1)

    def step(self, action):
        dev = self.dev; s = self.s.long()
        correct = (action == s).float()
        is_gren = (action == 1).float(); is_smoke = (action == 3).float()
        avail = (1 - is_gren * (self.grenades <= 0).float() - is_smoke * (self.smoke <= 0).float()).clamp(0, 1)
        effective = correct * avail * self.alive
        self.grenades = (self.grenades - is_gren).clamp(min=0)          # consommé même si mal employé
        self.smoke = (self.smoke - is_smoke).clamp(min=0)
        self.cleared = self.cleared + effective
        dangerous = ((s == 2) | (s == 4)).float(); wrong = 1 - correct
        hit = (torch.rand(self.N, device=dev) < dangerous * wrong * 0.3).float()   # mauvais outil en situation dangereuse = riposte
        self.alive = self.alive * (1 - hit)
        r = (effective * 3.0 + effective * 1.0                          # franchir + PRIME À L'USAGE
             - wrong * 0.3 - is_gren * (1 - correct) * 1.0 - is_smoke * (1 - correct) * 1.0   # gaspiller un consommable
             - hit * 4.0 - 0.05)
        newidx = torch.where(effective > 0)[0]                          # situation suivante quand franchie
        if newidx.numel() > 0: self._gen(newidx)
        self.t += 1
        timeout = (self.t >= self.max_steps) & (self.cleared < self.K)
        r = r - timeout.float() * 3.0
        done = (self.cleared >= self.K) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"cleared": (self.cleared / self.K).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
