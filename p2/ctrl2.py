"""CONTROLE 2 + LE PAS CHRONOMETRE. Criteres ecrits avant.
Le champ `reached` n existe plus dans `info` (c est `took`) : scripted_compare.py est
lui aussi perime, independamment du plantage.
PREDICTION : `cible_unique=True` (un defenseur tire sur UN homme) doit donner
STRICTEMENT MOINS de pertes que False. Sinon la branche est inerte."""
import math, sys, time, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


def joue(cible_unique, N=1024, steps=60, seed=11, dev="cuda:0"):
    e = AssaultTerrain(num_envs=N, relief=40.0, hit=0.10, device=dev, seed=seed,
                       cible_unique=cible_unique)
    e.reset()
    pertes = prise = 0.0; nep = 0
    for _ in range(steps):
        bear = torch.atan2(-e.apx, -e.apy)
        _, r, done, info = e.step((torch.round(bear / (math.pi / 4)) % 8).long())
        dm = done.bool()
        if dm.any():
            pertes += info["losses"][dm].sum().item()
            prise += info["took"][dm].float().sum().item()
            nep += int(dm.sum())
    return pertes / max(nep, 1), prise / max(nep, 1), nep


pu, au, nu = joue(True)
pt, at, nt = joue(False)
print("   cible_unique=True  : pertes %.3f  prise %.3f  (%d ep)" % (pu, au, nu))
print("   cible_unique=False : pertes %.3f  prise %.3f  (%d ep)" % (pt, at, nt))
print("   CONTROLE=%s" % ("PASSE" if pu < pt else "ECHOUE_branche_inerte"))

print("=== 3. LE PAS, chronometre a l echelle du banc de debit ===")


def chrono(N, steps=30, echauffe=5):
    e = AssaultTerrain(num_envs=N, relief=40.0, hit=0.10, device="cuda:0", seed=11)
    e.reset()

    def pas():
        bear = torch.atan2(-e.apx, -e.apy)
        e.step((torch.round(bear / (math.pi / 4)) % 8).long())

    for _ in range(echauffe):
        pas()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(steps):
        pas()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / steps * 1e3, e.A


ms, A = chrono(4096)
ms4, _ = chrono(1024)
print("   PAS 4096 env x %d attaquants : %.2f ms/pas  (%.0f pas-env/s)" % (A, ms, 4096 / (ms * 1e-3)))
print("   PAS 1024 env               : %.2f ms/pas  -> rapport %.2f" % (ms4, ms / ms4))
print("   PAS_VERDICT=%s" % ("MESURE" if ms > ms4 * 1.2 else "TOMBE_insensible_a_la_taille"))
print("   LOS boites 185 = 8.72 ms -> %.0f %% d un pas" % (8.72 / ms * 100))
print("   LOS boites 5000 = 121.13 ms -> %.0f %% d un pas" % (121.13 / ms * 100))
