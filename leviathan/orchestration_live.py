#!/usr/bin/env python3
"""orchestration_live.py — ETAPE 4 : la TETE de selection (orchestration_voyant.pt, reuse DIRECT).
Classifieur de situation (perception Arma -> type 0-4) -> obs[8] = one-hot[5] + gren/2 + fumi/2 + progres
-> orchestration_voyant.pt -> argmax -> tactique.
Mapping (1:1, valide) : 0=TIR_VISE 1=GRENADE 2=FLANC 3=FUMIGENE 4=SUPPRESSION
                         (types EXPOSE / COUVERT / RETRANCHE / A_DECOUVERT / CLOUE)."""
import math, torch, torch.nn as nn

CKPT = "/home/younes/arma3-marl/leviathan/orchestration_voyant.pt"


class OrchNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.b = nn.Sequential(nn.Linear(8, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.a = nn.Linear(128, 5); self.v = nn.Linear(128, 1)

    def forward(self, x):
        h = self.b(x); return self.a(h), self.v(h)


class Orchestrator:
    def __init__(self, ckpt=CKPT, device="cpu"):
        self.net = OrchNet().to(device)
        self.net.load_state_dict(torch.load(ckpt, map_location=device)); self.net.eval()
        self.dev = device

    @staticmethod
    def classify(pos, enemies, thr, cover):
        """perception -> type. pos[x,y], enemies[[x,y]], thr 0-1 (sous feu/expo), cover 0-1 (mon couvert)."""
        if not enemies:
            return 0
        d = min(math.hypot(pos[0] - e[0], pos[1] - e[1]) for e in enemies)
        if thr > 0.7:      return 4        # CLOUE (feu nourri)            -> suppression
        if d <= 40:        return 1        # COUVERT (ennemi proche)       -> grenade
        if d > 150:        return 2        # RETRANCHE (ennemi loin)       -> flanc
        if cover < 0.25:   return 3        # A DECOUVERT (peu de couvert)  -> fumigene
        return 0                           # EXPOSE (tir possible)         -> tir vise

    @torch.no_grad()
    def select(self, agents):
        """agents: [{pos, enemies, thr, cover, gren, smoke, progress}] -> [tactique 0-4]."""
        if not agents:
            return []
        obs = []
        for a in agents:
            t = Orchestrator.classify(a["pos"], a["enemies"], a["thr"], a["cover"])
            oh = [0.0] * 5; oh[t] = 1.0
            obs.append(oh + [min(a.get("gren", 2) / 2.0, 1.0),
                             min(a.get("smoke", 1) / 2.0, 1.0),
                             a.get("progress", 0.5)])
        logits, _ = self.net(torch.tensor(obs, dtype=torch.float32, device=self.dev))
        return logits.argmax(1).tolist()
