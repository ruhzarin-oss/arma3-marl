#!/usr/bin/env python3
"""q11_gym.py — le MEME cadran cote gymnase : survie d un homme expose sous le feu de huit.

Rien n est regle ici : on lit. L homme est debout (posture 0), immobile (action 8 = HOLD),
sur terrain PLAT et decouvert, a distance fixe de huit defenseurs alignes. On compte les pas
jusqu a sa mort, on convertit en secondes (1 pas = 3,28 s).
"""
import sys, torch
sys.path.insert(0, '/home/younes/arma3-marl')
from assault_terrain import AssaultTerrain

PAS_S = 3.28
N = 1024
MAX_PAS = 24          # 78 s, au-dela on declare qu il survit

print('=== Q11 gymnase — survie d un homme expose, 8 defenseurs, terrain plat ===')
print('  %8s %16s %14s' % ('distance', 'survie mediane', 'morts / 1024'))
for dist in (30.0, 60.0, 100.0):
    for alerte in (True,):
        env = AssaultTerrain(num_envs=N, A=1, D=8, relief=0.0, alerte=alerte,
                             cible_unique=True, device="cuda:0")
        env.reset()
        d = env.dev
        # geometrie imposee : ligne de huit, attaquant plein sud a distance fixe
        for i in range(8):
            env.dpx[:, i] = (i - 4) * 25.0
            env.dpy[:, i] = 0.0
        env.apx[:, 0] = 0.0
        env.apy[:, 0] = -dist
        mort_au = torch.full((N,), -1, device=d, dtype=torch.long)
        hold = torch.full((N, 1), 8, device=d, dtype=torch.long)
        for p in range(1, MAX_PAS + 1):
            env.apx[:, 0] = 0.0; env.apy[:, 0] = -dist     # il ne bouge pas
            env.step(hold, auto_reset=False)
            vivant = env._aalive()[:, 0]
            neuf = (~vivant) & (mort_au < 0)
            mort_au[neuf] = p
        morts = (mort_au > 0)
        n_morts = int(morts.sum())
        if n_morts > N // 2:
            med = float(mort_au[morts].float().median()) * PAS_S
            print('  %6.0f m %13.1f s %10d / %d' % (dist, med, n_morts, N), flush=True)
        else:
            print('  %6.0f m   survit %d s %8d / %d' % (dist, int(MAX_PAS * PAS_S), n_morts, N), flush=True)
        del env
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
print('GYM_DONE')
