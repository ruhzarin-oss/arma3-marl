#!/usr/bin/env python3
"""calib_sandbox.py — PORTE DE CALIBRATION (Fable). Mesure la LÉTALITÉ DÉFENSEUR × DISTANCE dans le sandbox :
des attaquants foncent vers l'objectif (avance pure), on compte où ils MEURENT (taux de mort par anneau de 10m).
Si le taux est PLAT -> le sandbox ne reproduit pas le mur balistique d'Arma (qui bascule en approchant) -> porte FERMÉE."""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"
e = AssaultTerrain(num_envs=2048, A=18, D=12, R_spawn=140.0, move=14.0, fire_range=110.0, hit=0.06,
                   secure_r=25.0, max_steps=55, device=DEV, seed=1)
e.reset()
NB = 16
deaths = torch.zeros(NB, device=DEV); expo = torch.zeros(NB, device=DEV)
prev = e.admg.clone()
for t in range(55):
    apx, apy = e.apx, e.apy
    cap = (torch.round(torch.atan2(-apx, -apy) / (math.pi / 4)) % 8).long()   # avance pure vers l'objectif (origine)
    e.step(cap, auto_reset=False)
    ndist = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    alive = e._aalive()
    band = (ndist / 10).long().clamp(0, NB - 1)
    expo += torch.bincount(band[alive].flatten(), minlength=NB).float()
    died = (e.admg >= e.dmg_dead) & (prev < e.dmg_dead)
    deaths += torch.bincount(band[died].flatten(), minlength=NB).float()
    prev = e.admg.clone()
rate = deaths / expo.clamp(min=1)
print("=== SANDBOX : létalité défenseur × distance (avance pure, 2048 envs) ===", flush=True)
print("  anneau(m)   morts   exposition   TAUX (morts/attaquant-tick)", flush=True)
for b in range(NB):
    if expo[b] > 0:
        print("   %3d-%3d :  %6.0f   %8.0f      %.4f" % (b * 10, b * 10 + 10, deaths[b].item(), expo[b].item(), rate[b].item()), flush=True)
# verdict : le taux monte-t-il en approchant (< 60m vs 60-110m) ?
near = rate[2:6][expo[2:6] > 0]; far = rate[6:11][expo[6:11] > 0]
mn = near.mean().item() if near.numel() else 0; mf = far.mean().item() if far.numel() else 0
print("\n  taux moyen LOIN (60-110m)=%.4f   PROCHE (20-60m)=%.4f   ratio proche/loin=%.2f" % (mf, mn, (mn / mf if mf > 0 else 0)), flush=True)
print("  >>> %s" % ("PLAT (ratio ~1) -> ne reproduit PAS Arma -> porte FERMÉE, il faut ajouter la létalité×distance" if mf > 0 and mn / mf < 1.5 else "monte en approchant -> proche d'Arma"), flush=True)
print("CALIB_DONE", flush=True)
