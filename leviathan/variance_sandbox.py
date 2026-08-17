#!/usr/bin/env python3
"""variance_sandbox.py — DE COMBIEN LE SANDBOX BOUGE-T-IL D UNE GRAINE A L AUTRE ?

Miroir de variance_banc.sh, cote sandbox. Tous les verdicts du 28/07 reposent sur la
GRAINE 7. Si le sandbox bouge de 20 points d une graine a l autre, le seuil de manoeuvre
D=8 n est pas un seuil, c est un tirage.

Criteres figes AVANT dans CRITERES_VARIANCE_SANDBOX.md.
"""
import sys, os, json, math, time, argparse, statistics
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from assault_terrain import AssaultTerrain
from manuel import MANOEUVRES

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--episodes', type=int, default=200)
ap.add_argument('--steps', type=int, default=60)
ap.add_argument('--graines', type=int, default=12)
ap.add_argument('--D', type=int, default=8)
ap.add_argument('--doctrine', default='debordement_simple')
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='variance_sandbox.json')
a = ap.parse_args()


def joue(seed):
    e = AssaultTerrain(num_envs=a.episodes, A=4, D=a.D, seed=seed, device=a.device,
                       max_steps=a.steps, postures=True, hull=True, def_line=True,
                       def_rand=True, secure_task=True, secure_only=True,
                       courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                       degat_par_impact=DEG, supp_residuel=0.08, supp_persist=0.35,
                       cible_unique=True)
    e.reset(); f = MANOEUVRES[a.doctrine]; N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    pertes = torch.zeros(N, device=e.dev)
    for t in range(a.steps):
        _, _, done, info = e.step(f(e, t), auto_reset=False)
        v = ~fini
        pris = pris | (info['took'] & v)
        pertes = torch.where(v, info['losses'].float(), pertes)
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    return float(pris.float().mean()), float(pertes.mean())


if __name__ == '__main__':
    if not os.path.exists(LEV + '/CRITERES_VARIANCE_SANDBOX.md'):
        print('!! criteres non figes — ARRET.'); sys.exit(2)
    print('=== VARIANCE DU SANDBOX : %d graines, D=%d, %s, %d episodes ==='
          % (a.graines, a.D, a.doctrine, a.episodes))
    print('  graine   prise   pertes')
    t0 = time.time(); pr = []; res = {}
    for s in range(1, a.graines + 1):
        p, l = joue(s); pr.append(100 * p); res[s] = {'prise': p, 'pertes': l}
        print('    %2d     %5.1f%%   %.2f' % (s, 100 * p, l), flush=True)
    et = max(pr) - min(pr); sd = statistics.stdev(pr)
    print('')
    print('  ETENDUE (meilleure - pire graine) : %.1f points' % et)
    print('  ecart-type entre graines          : %.1f points' % sd)
    print('  moyenne                           : %.1f%%' % (sum(pr) / len(pr)))
    # REVUE 17/08 : `res[s]['prise']` est une FRACTION (0-1) ; le %% l affichait 100 fois
    # trop petit — une prise de 40 %% s imprimait « 0,4 %% » sur la ligne meme qui sert
    # d ancrage aux verdicts du 28/07.
    print('  (rappel : tous les verdicts du 28/07 reposent sur la GRAINE 7 = %.1f%%)' % (100 * res[7]['prise']) if 7 in res else '')
    print('')
    print('=== LECTURE (criteres figes) ===')
    if et <= 5:
        print('  >>> SANDBOX STABLE : une graine suffit, les verdicts du 28/07 tiennent tels quels.')
    elif et <= 15:
        print('  >>> RAPPORTER UNE MOYENNE SUR >=5 GRAINES. Les verdicts du 28/07 restent valides')
        print('      en DIRECTION, mais leurs chiffres sont a re-publier en moyenne.')
    else:
        print('  >>> LE SEUIL D=8 N EST PAS UN SEUIL, C EST UN TIRAGE (etendue %.1f > 15).' % et)
        print('      Tous les verdicts sandbox du 28/07 sont a refaire en multi-graines')
        print('      avant d etre cites.')
    json.dump({'criteres': 'CRITERES_VARIANCE_SANDBOX.md', 'graines': res,
               'etendue': et, 'ecart_type': sd, 'duree_s': round(time.time() - t0)},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('\n-> %s/%s  (%.0f s)' % (LEV, a.out, time.time() - t0))
    print('VARIANCE_SANDBOX_DONE')
