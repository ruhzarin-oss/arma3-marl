"""Le PAS du gymnase, chronometre — le denominateur qui manquait au banc de debit.
Boucle reprise MOT POUR MOT de scripted_compare.py (politique aveugle), la seule
dont on sait qu elle tourne. Mes actions tirees au hasard faisaient sortir un indice
des bornes dans _reset : on ne chronometre pas un monde qu on vient de casser."""
import math, time, torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

DEV = "cuda:0"


def mesure(N, steps=30, echauffe=5):
    e = AssaultTerrain(num_envs=N, relief=40.0, hit=0.10, device=DEV, seed=11)
    e.reset()

    def un_pas():
        bear = torch.atan2(-e.apx, -e.apy)
        a = (torch.round(bear / (math.pi / 4)) % 8).long()
        e.step(a)

    for _ in range(echauffe):
        un_pas()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(steps):
        un_pas()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / steps * 1e3, e.A


ms, A = mesure(4096)
print("PAS gymnase      : %.2f ms/pas  (4096 env x %d attaquants)" % (ms, A))
print("PAS debit        : %.0f pas-environnement/s" % (4096 / (ms * 1e-3)))
ms4, _ = mesure(1024)
print("PAS a 1024 env   : %.2f ms/pas  -> rapport %.2f" % (ms4, ms / ms4))
print("PAS_VERDICT=%s" % ("MESURE" if ms > ms4 * 1.2 else "TOMBE_insensible_a_la_taille"))
