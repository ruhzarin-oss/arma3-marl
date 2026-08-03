#!/usr/bin/env python3
"""test_alerte.py — LE GYMNASE ECHOUE-T-IL AU MEME ENDROIT QUE LE JUGE ?

Critere (CRITERES_ALERTE_GYM.md 417252605cfd14d1) : a A=4 contre D=8, debordement, le taux de
prise doit tomber dans [0 ; 8,8 %], l intervalle de Wilson du juge (0 prise sur 40 operations).

Deux garde-fous : a A=24 le gymnase doit encore rendre plus de 5 %, sinon il est devenu
IMPOSSIBLE au lieu de devenu DIFFICILE. Et l ordre des doctrines doit etre preserve.
"""
import sys, math
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from assault_terrain import AssaultTerrain
from manuel import MANOEUVRES

LEV = '/home/younes/arma3-marl/leviathan'


def joue(f, A, alerte, n=1024, graine=3):
    e = AssaultTerrain(num_envs=n, A=A, D=8, seed=graine, device='cuda:0', max_steps=80,
                       postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                       def_rand=True, secure_task=True, secure_only=True, alerte=alerte,
                       courbe=LEV + '/courbe_toucher_juge.json',
                       tir_par_pas=1.15, sec_par_pas=3.28, degat_par_impact=0.233,
                       supp_residuel=0.08, supp_persist=0.35, cible_unique=True)
    e.reset()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(80):
        _, _, d, info = e.step(f(e, t), auto_reset=False)
        pris |= info['took'] & ~fini
        fini |= d.bool()
    al = float(e.alerte_niv.mean()) if alerte else 0.0
    return 100.0 * float(pris.float().mean()), al


print('=== LE GYMNASE AVEC ET SANS LE MODELE D ALERTE ===')
print('  cible a A=4 : intervalle du juge [0,0 ; 8,8] %%')
print()
print('  %-22s %6s %10s %10s %12s' % ('doctrine', 'A', 'SANS', 'AVEC', 'alerte moy'))
for nom, f in MANOEUVRES.items():
    for A in (4, 24):
        t0, _ = joue(f, A, False)
        t1, al = joue(f, A, True)
        m = ''
        if A == 4 and 0.0 <= t1 <= 8.8:
            m = '  <- DANS L INTERVALLE'
        print('  %-22s %6d %9.1f%% %9.1f%% %11.2f%s' % (nom, A, t0, t1, al, m), flush=True)
print()
print('=== LECTURE ===')
d4, al4 = joue(MANOEUVRES['debordement_double'], 4, True)
d24, _ = joue(MANOEUVRES['debordement_double'], 24, True)
print('  debordement double : A=4 -> %.1f%% | A=24 -> %.1f%%' % (d4, d24))
if 0.0 <= d4 <= 8.8 and d24 > 5.0:
    print('  >>> CRITERE FRANCHI. Le gymnase echoue au meme endroit que le juge,')
    print('      et rend encore quelque chose a fort effectif.')
elif d4 > 8.8:
    print('  >>> ENCORE COMPLAISANT : %.1f%% contre au plus 8,8 attendus.' % d4)
else:
    print('  >>> DEVENU IMPOSSIBLE : A=24 ne rend que %.1f%%. On a casse au lieu de reparer.' % d24)
print('TEST_ALERTE_DONE')
