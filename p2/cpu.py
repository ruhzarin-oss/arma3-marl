"""Reproduction sur CPU : le GPU ne rend qu une assertion, le CPU rend l INDICE fautif."""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

e = AssaultTerrain(num_envs=256, relief=40.0, hit=0.10, device="cpu", seed=11)
e.reset()
print("A =", e.A, " D =", e.D)
for i in range(60):
    bear = torch.atan2(-e.apx, -e.apy)
    a = (torch.round(bear / (math.pi / 4)) % 8).long()
    try:
        e.step(a)
    except Exception as ex:
        print("PAS %d : %s" % (i, type(ex).__name__))
        print("  %s" % str(ex)[:300])
        break
else:
    print("60 pas sans erreur sur CPU")
