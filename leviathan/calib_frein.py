#!/usr/bin/env python3
"""calib_frein.py — CALIBRER LE FREIN SUR L ISSUE, pas au jugement.

Critere d acceptation (CRITERES_REPARATION_GYM.md 3c3c304562af45de) : a A=4 contre D=8, le
gymnase doit tomber dans l intervalle de Wilson du juge, [0 ; 8,8 %]. Le but n est pas de faire
reussir le gymnase, c est de le faire ECHOUER AU MEME ENDROIT.

Garde-fou : viser l intervalle, jamais zero. Un gymnase impossible ne vaut pas mieux qu un
gymnase complaisant — on verifie donc qu a A=24 il rend encore quelque chose.
"""
import sys, math
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from assault_terrain import AssaultTerrain
from manuel import debordement_double

LEV = '/home/younes/arma3-marl/leviathan'
JUGE_LO, JUGE_HI = 0.0, 8.8


def taux(frein, A, graine=3, n=1024):
    e = AssaultTerrain(num_envs=n, A=A, D=8, seed=graine, device='cuda:0', max_steps=80,
                       postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                       def_rand=True, secure_task=True, secure_only=True, frein_feu=frein,
                       courbe=LEV + '/courbe_toucher_juge.json',
                       tir_par_pas=1.15, sec_par_pas=3.28, degat_par_impact=0.233,
                       supp_residuel=0.08, supp_persist=0.35, cible_unique=True)
    e.reset()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    for t in range(80):
        _, _, d, info = e.step(debordement_double(e, t), auto_reset=False)
        pris |= info['took'] & ~fini
        dd = torch.sqrt(e.apx ** 2 + e.apy ** 2).min(1).values
        dmin = torch.minimum(dmin, torch.where(fini, dmin, dd))
        fini |= d.bool()
    return 100.0 * float(pris.float().mean()), float(dmin.median())


print('=== CALIBRAGE DU FREIN SUR L ISSUE — cible : A=4 dans [%.1f ; %.1f] %% ===' % (JUGE_LO, JUGE_HI))
print('  %7s %12s %14s %14s' % ('frein', 'A=4 prise', 'A=4 dist min', 'A=24 prise'))
bon = None
for fr in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
    t4, d4 = taux(fr, 4)
    t24, _ = taux(fr, 24)
    marque = ''
    if JUGE_LO <= t4 <= JUGE_HI:
        marque = '  <- DANS L INTERVALLE'
        if bon is None and t24 > 5.0:
            bon = fr
    print('  %7.1f %11.1f%% %11.0f m %11.1f%%%s' % (fr, t4, d4, t24, marque), flush=True)
print('')
print('  juge : A=4 -> 0,0 %% (n=40, dist min mediane 74 m) | A=8 -> 5,6 %% (n=36, 60 m)')
print('')
print('=== LECTURE ===')
if bon is not None:
    print('  >>> FREIN RETENU : %.1f — le gymnase echoue au meme endroit que le juge,' % bon)
    print('      et rend encore quelque chose a fort effectif.')
else:
    print('  >>> AUCUN FREIN NE SATISFAIT LES DEUX CONDITIONS. Soit le gymnase reste complaisant,')
    print('      soit il devient impossible. Le frein seul ne suffit pas.')
print('CALIB_FREIN_DONE')
