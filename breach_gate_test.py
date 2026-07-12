"""TEST DU GATE (idee Younes) : un poids g(situation) module l'attention.
g bas = mode AUDACIEUX (l'attention recule, le soldat commet son geste) ;
g haut = mode COORDINATION (il regarde ses voisins). g est APPRIS depuis la situation (hp, in-band, dist obj).
Objectif : voir si le gate rend attention+audace FIABLE (variance basse) vs le 0.67 +/- 0.47 instable.
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import numpy as np, torch, torch.nn as nn
from breach_test import Breach, AttnActor, Critic, train, DEV

class GatedAttnActor(nn.Module):
    def __init__(self, od, na, H=64, heads=4):
        super().__init__()
        self.own = nn.Sequential(nn.Linear(od, H), nn.Tanh())
        self.kv = nn.Linear(3, H)
        self.attn = nn.MultiheadAttention(H, heads, batch_first=True)
        self.gate = nn.Sequential(nn.Linear(od, H // 2), nn.Tanh(), nn.Linear(H // 2, 1), nn.Sigmoid())
        self.head = nn.Sequential(nn.Linear(2 * H, H), nn.Tanh(), nn.Linear(H, na))
    def logits(self, of, ot):
        N, A, _, _ = ot.shape
        q = self.own(of); kv = torch.tanh(self.kv(ot))
        ctx, _ = self.attn(q.reshape(N * A, 1, -1), kv.reshape(N * A, A, -1), kv.reshape(N * A, A, -1))
        g = self.gate(of)                                   # (N,A,1) : combien coordonner ici/maintenant
        return self.head(torch.cat([q, g * ctx.reshape(N, A, -1)], -1))

if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 8 if SMOKE else 300
    SEEDS = [0, 1] if SMOKE else [0, 1, 2, 3, 4, 5]
    print("=== GATE TEST : attention vs GATED (regime AUDACE, %d graines) ===" % len(SEEDS), flush=True)
    res = {}
    for name, cls in [("attention", AttnActor), ("gated", GatedAttnActor)]:
        b, c = [], []
        for s in SEEDS:
            br, cs = train(cls, True, seed=s, iters=ITERS); b.append(br); c.append(cs)
            print("[%s] seed %d -> perce %.2f pertes %.2f" % (name, s, br, cs), flush=True)
        res[name] = (np.mean(b), np.std(b), np.mean(c))
        print(">>> %s : perce %.2f +/- %.2f | pertes %.2f" % (name, np.mean(b), np.std(b), np.mean(c)), flush=True)
    print("\n===== %d graines, regime audace =====" % len(SEEDS), flush=True)
    for k, (m, s, c) in res.items():
        print("%-10s | perce %.2f +/- %.2f | pertes %.2f" % (k, m, s, c), flush=True)
    print("GATE_DONE", flush=True)
