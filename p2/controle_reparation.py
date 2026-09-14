"""CONTROLE DE LA REPARATION — criteres ecrits AVANT de lancer.

1. JUSTESSE DE FORME : 60 pas sur CPU sans erreur (le plantage se produisait au pas 2).
2. LA BRANCHE FAIT CE QU ELLE DIT : a graine et monde identiques, `cible_unique=True`
   (un defenseur tire sur UN homme) doit donner STRICTEMENT MOINS de pertes que
   `cible_unique=False` (chaque defenseur bat tous ceux qu il voit).
   ⛔ ECHEC si les pertes sont egales ou superieures : la branche serait inerte, et
   la reparation n aurait retabli qu un silence.
"""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


def joue(cible_unique, N=1024, steps=60, seed=11, dev="cuda:0"):
    e = AssaultTerrain(num_envs=N, relief=40.0, hit=0.10, device=dev, seed=seed,
                       cible_unique=cible_unique)
    e.reset()
    pertes = 0.0; nep = 0; atteint = 0.0
    for _ in range(steps):
        bear = torch.atan2(-e.apx, -e.apy)
        a = (torch.round(bear / (math.pi / 4)) % 8).long()
        _, r, done, info = e.step(a)
        dm = done.bool()
        if dm.any():
            pertes += info["losses"][dm].sum().item()
            atteint += info["reached"][dm].float().sum().item()
            nep += int(dm.sum())
    return pertes / max(nep, 1), atteint / max(nep, 1), nep


print("=== 1. justesse de forme, 60 pas sur CPU ===")
e = AssaultTerrain(num_envs=256, relief=40.0, hit=0.10, device="cpu", seed=11); e.reset()
for i in range(60):
    bear = torch.atan2(-e.apx, -e.apy)
    e.step((torch.round(bear / (math.pi / 4)) % 8).long())
print("   60 pas sans erreur : OK")

print("=== 2. la branche fait-elle quelque chose ? ===")
pu, au, nu = joue(True)
pt, at, nt = joue(False)
print("   cible_unique=True  : pertes %.3f  objectif %.3f  (%d episodes)" % (pu, au, nu))
print("   cible_unique=False : pertes %.3f  objectif %.3f  (%d episodes)" % (pt, at, nt))
print("   CONTROLE=%s" % ("PASSE" if pu < pt else "ECHOUE_branche_inerte"))
