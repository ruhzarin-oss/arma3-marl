#!/usr/bin/env python3
"""calib_gym.py — le cote GYMNASE de la courbe de calibration sur l issue.
Meme manoeuvre, memes defenseurs, on fait varier les attaquants. Metrique unique : la prise.
Criteres : CRITERES_CALIBRATION_ISSUE.md (162338a0f996a435)
"""
import sys, math
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from assault_terrain import AssaultTerrain
from manuel import debordement_double

LEV = '/home/younes/arma3-marl/leviathan'
print('=== COTE GYMNASE — debordement, D=8, 1024 episodes par point ===')
print('  %4s %10s' % ('A', 'prise'))
for A in (4, 8, 12, 18, 24):
    e = AssaultTerrain(num_envs=1024, A=A, D=8, seed=3, device='cuda:0', max_steps=80,
                       postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                       def_rand=True, secure_task=True, secure_only=True,
                       courbe=LEV + '/courbe_toucher_juge.json',
                       tir_par_pas=1.15, sec_par_pas=3.28, degat_par_impact=0.233,
                       supp_residuel=0.08, supp_persist=0.35, cible_unique=True)
    e.reset()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(80):
        _, _, d, info = e.step(debordement_double(e, t), auto_reset=False)
        pris |= info['took'] & ~fini
        fini |= d.bool()
    print('  %4d %9.1f%%' % (A, 100.0 * float(pris.float().mean())), flush=True)
print('CALIB_GYM_DONE')
