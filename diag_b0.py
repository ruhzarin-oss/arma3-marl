#!/usr/bin/env python3
"""diag_b0 — POURQUOI la doctrine du gymnase ne fait que 81,3 % la ou Arma fait 100 % ?

Hypothese a tester, une seule : LE GYMNASE A UN QUANTUM DE DEPLACEMENT DE 14 m
(move=14, SEC_PAR_PAS=3,28). Un rayon de prise de 6 m est PLUS PETIT que son pas.
L'agent enjambe l'objectif au lieu d'y arriver. Ce ne serait pas un defaut de physique,
ce serait un defaut de RESOLUTION.

Trois configurations. La premiere est la replique fidele, les deux autres l'instruisent.
  A  D= 30 m, rayon  6 m  -> la replique du palier 30 (rayon < quantum)
  B  D= 30 m, rayon 15 m  -> ATTRIBUTION : meme monde, rayon > quantum
  C  D=150 m, rayon 15 m  -> la replique du palier 150, cible Arma [91,6;100] / [0;8,4] / [0;8,4]
"""
import sys, math, json, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

DEV, N = "cuda:0", 2000

def wilson(k, n, z=1.96):
    ph = k/n; d = 1+z*z/n
    c = (ph+z*z/(2*n))/d; h = z*((ph*(1-ph)/n + z*z/(4*n*n))**0.5)/d
    return (max(0.,c-h)*100, min(1.,c+h)*100)

def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy)/(math.pi/4.0)).long() % 8)

def jouer(nom, R, rayon, pas):
    cfg = dict(MONDE_ARMA); cfg.update(dict(secure_only=True, postures=True))
    e = AssaultTerrain(num_envs=N, A=1, D=1, D_min=1, R_spawn=float(R),
                       secure_r=float(rayon), max_steps=pas, device=DEV, seed=7, **cfg)
    e.reset(); e.ddmg[:] = 0.95
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    dmin = torch.sqrt(e.apx**2 + e.apy**2).mean(1).clone()
    for t in range(pas):
        vers = cap(-e.apx, -e.apy)
        if nom == "NOOP":
            a = torch.full_like(vers, 8)
        elif nom == "ALEATOIRE":
            g = torch.randint(0, 13, vers.shape, device=e.dev)
            a = torch.where(g == 8, vers, g)
        else:
            a = vers
        _, _, done, info = e.step(a, auto_reset=False)
        pris |= info["took"] & ~fini
        fini |= done.bool()
        d = torch.sqrt(e.apx**2 + e.apy**2).mean(1)
        dmin = torch.minimum(dmin, d)
        if bool(fini.all()): break
    return float(pris.float().mean())*100, int(pris.sum()), float(dmin.mean())

CIBLES = {30: {"DOCTRINE": (93.0,100.0), "ALEATOIRE": (5.5,23.4), "NOOP": (0.0,7.0)},
          150:{"DOCTRINE": (91.6,100.0), "ALEATOIRE": (0.0, 8.4), "NOOP": (0.0,8.4)}}

for tag, R, rayon, pas, cible in [
        ("A  replique 30 m (rayon 6 < quantum 14)", 30, 6,  6,  CIBLES[30]),
        ("B  attribution 30 m (rayon 15 > quantum)", 30, 15, 6,  None),
        ("C  replique 150 m (rayon 15 > quantum)",  150, 15, 23, CIBLES[150])]:
    print(f"\n=== {tag} ===")
    for nom in ["DOCTRINE", "ALEATOIRE", "NOOP"]:
        taux, k, dm = jouer(nom, R, rayon, pas)
        lo, hi = wilson(k, N)
        if cible:
            alo, ahi = cible[nom]
            v = "DANS" if alo <= taux <= ahi else "HORS"
            print(f"  {nom:10s} {taux:6.1f}% [{lo:5.1f};{hi:5.1f}]   Arma [{alo:5.1f};{ahi:5.1f}]  approche_min {dm:5.1f} m  {v}")
        else:
            print(f"  {nom:10s} {taux:6.1f}% [{lo:5.1f};{hi:5.1f}]   approche_min {dm:5.1f} m")
