"""Isole la VALEUR de la perception (sans confond RL) : politique scriptee AVEUGLE (cap sur objectif tout droit)
vs PERCEPTION (parmi les caps qui progressent, choisir celui dont la case suivante a le plus de COUVERT)."""
import math, torch
from assault_terrain import AssaultTerrain
import terrain_gpu as TG
dev = "cuda:0"

def run(policy, relief=40.0, hit=0.10, N=2048, steps=60, seed=11):
    e = AssaultTerrain(num_envs=N, relief=relief, hit=hit, device=dev, seed=seed); e.reset()
    reach = wipe = loss = 0.0; nep = 0
    for _ in range(steps):
        bear = torch.atan2(-e.apx, -e.apy)
        base = (torch.round(bear / (math.pi / 4)) % 8).long()
        if policy == "aveugle":
            a = base
        else:  # perception : parmi cap, cap +/-1 (toujours vers l'objectif), prendre la case suivante la + couverte
            best = base.clone(); bestc = torch.full_like(e.apx, -1.0)
            for off in (-1, 0, 1):
                h = (base + off) % 8; th = h.float() * (math.pi / 4)
                nx = (e.apx + torch.sin(th) * e.move).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
                ny = (e.apy + torch.cos(th) * e.move).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
                cov = TG.sample(e.cover, nx, ny, e.terr_R)
                better = cov > bestc; best = torch.where(better, h, best); bestc = torch.where(better, cov, bestc)
            a = best
        _, r, done, info = e.step(a); dm = done.bool()
        if dm.any():
            reach += info["reached"][dm].float().sum().item(); wipe += info["wiped"][dm].float().sum().item()
            loss += info["losses"][dm].sum().item(); nep += int(dm.sum())
    return reach / max(nep, 1), wipe / max(nep, 1), loss / max(nep, 1), nep

print("ISOLATION valeur perception (scripte, relief 40, hit 0.10) :")
res = {}
for pol in ["aveugle", "perception"]:
    pr, pw, pl, n = run(pol); res[pol] = pr
    print("  %-11s : objectif atteint %.0f%% | aneanti %.0f%% | pertes %.0f%% (%d ep)" % (pol, 100 * pr, 100 * pw, 100 * pl, n))
print("ECART perception - aveugle = %+.0f pts" % (100 * (res["perception"] - res["aveugle"])))
print(">>> %s" % ("PERCEPTION A DE LA VALEUR (le RL doit juste apprendre a s'en servir)" if res["perception"] - res["aveugle"] >= 0.08 else "perception sans valeur meme utilisee -> la tache/terrain ne la recompense pas"))
