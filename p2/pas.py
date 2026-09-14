"""Le PAS du gymnase, chronometre — le denominateur qui manquait au banc de debit.
Meme echelle que banc_debit.py : 4096 environnements, 3 attaquants."""
import time, torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

DEV = "cuda:0"
N, A, D = 4096, 3, 4
e = AssaultTerrain(num_envs=N, A=A, D=D, device=DEV, seed=0, max_steps=60)
e.reset()
g = torch.Generator(device=DEV).manual_seed(0)


def un_pas():
    a = torch.randint(0, 8, (N, A), generator=g, device=DEV)
    e.step(a)


for _ in range(5):                      # echauffement : les premiers pas allouent
    un_pas()
torch.cuda.synchronize()
t0 = time.perf_counter()
n = 30
for _ in range(n):
    un_pas()
torch.cuda.synchronize()
ms = (time.perf_counter() - t0) / n * 1e3
print("PAS gymnase      : %.2f ms/pas  (%d env x %d attaquants)" % (ms, N, A))
print("PAS debit        : %.0f pas-environnement/s" % (N / (ms * 1e-3)))
# CONTROLE : le temps doit CROITRE avec le nombre d environnements. S il ne bouge pas,
# je ne chronometre pas le calcul mais la file d attente asynchrone du GPU.
e2 = AssaultTerrain(num_envs=N // 4, A=A, D=D, device=DEV, seed=0, max_steps=60); e2.reset()
g2 = torch.Generator(device=DEV).manual_seed(0)
for _ in range(5):
    e2.step(torch.randint(0, 8, (N // 4, A), generator=g2, device=DEV))
torch.cuda.synchronize()
t0 = time.perf_counter()
for _ in range(n):
    e2.step(torch.randint(0, 8, (N // 4, A), generator=g2, device=DEV))
torch.cuda.synchronize()
ms4 = (time.perf_counter() - t0) / n * 1e3
print("PAS a N/4        : %.2f ms/pas  -> rapport %.2f (attendu > 1, sinon la mesure est fausse)" % (ms4, ms / ms4))
print("PAS_VERDICT=%s" % ("MESURE" if ms > ms4 else "TOMBE_mesure_insensible_a_la_taille"))
