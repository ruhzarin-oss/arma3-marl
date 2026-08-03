#!/usr/bin/env python3
"""preuve_permutation.py — PORTE E1 DU JALON 1.

Ne mesure rien, ne conclut rien sur un agent. Prouve UNE chose :
sous permutation, l observation ne differe QUE sur les quatre colonnes du verbe.

Motif : la v1 calculait la permutation AVANT le pas et la consommait APRES le re-tirage
de mission. Pour tout environnement qui venait de finir, l ordre affichait la permutation
d un verbe qui n existait deja plus. Cette preuve ferme cette classe de bug.

Protocole : deux mondes identiques, meme graine, memes actions, l un en ordre vrai,
l autre permute. La permutation ne touche que l OBSERVATION, jamais la dynamique :
tout le reste doit etre rigoureusement egal.
"""
import sys
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from monde_mission import fabrique, DIM_ORDRE, N_VERBES

VERBE = slice(-DIM_ORDRE, -DIM_ORDRE + N_VERBES)     # les 4 colonnes du verbe
RESTE_A = slice(0, -DIM_ORDRE)                        # tout ce qui precede l ordre
RESTE_B = slice(-DIM_ORDRE + N_VERBES, None)          # la fin de l ordre


def preuve(auto_reset, pas=5, envs=64, graine=11):
    a = fabrique(episodes=envs, D=8, seed=graine, steps=80)
    b = fabrique(episodes=envs, D=8, seed=graine, steps=80)
    oa = a.reset(permute=0)
    ob = b.reset(permute=1)
    g = torch.Generator(device=oa.device); g.manual_seed(999)
    for t in range(pas):
        acts = torch.randint(0, a.n_actions, (a.N, a.A), generator=g, device=oa.device)
        if not torch.equal(oa[..., RESTE_A], ob[..., RESTE_A]):
            return False, 'pas %d : le monde lui-meme differe' % t
        if not torch.equal(oa[..., RESTE_B], ob[..., RESTE_B]):
            return False, 'pas %d : l ordre differe AILLEURS que sur le verbe' % t
        if torch.equal(oa[..., VERBE], ob[..., VERBE]):
            return False, 'pas %d : le verbe affiche est IDENTIQUE — la permutation ne fait rien' % t
        oa, _, _, _ = a.step(acts, permute=0, auto_reset=auto_reset)
        ob, _, _, _ = b.step(acts, permute=1, auto_reset=auto_reset)
    return True, 'les %d pas ne different QUE sur les colonnes du verbe' % pas


if __name__ == '__main__':
    tout = True
    for mode, ar in (('episode  (auto_reset=False)', False), ('continu  (auto_reset=True)', True)):
        ok, msg = preuve(ar)
        print('  %-28s : %s — %s' % (mode, 'OK' if ok else 'ECHEC', msg))
        tout = tout and ok
    print('')
    print('PORTE E1 : ' + ('FRANCHIE' if tout else 'REFUSEE — on n avance pas'))
    sys.exit(0 if tout else 1)
