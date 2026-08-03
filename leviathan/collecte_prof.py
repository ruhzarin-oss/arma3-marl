#!/usr/bin/env python3
"""collecte_prof.py — collecte les paires etat-action du PROFESSEUR.

Un seul professeur : debordement_double, arrivee 96,2 %. Pas de melange de doctrines — sur
des caps discrets, un melange donne une distribution multimodale dont l argmax est un cap
absurde.

Filtre sur les episodes qui ARRIVENT, pas sur ceux qui reussissent : le respect du budget est
le travail du multiplicateur, pas du clonage.
"""
import sys, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from monde_mission import fabrique
from manuel import MANOEUVRES

ap = argparse.ArgumentParser()
ap.add_argument('--prof', default='debordement_double')
ap.add_argument('--envs', type=int, default=4096)
ap.add_argument('--paquets', type=int, default=12)
ap.add_argument('--pas', type=int, default=80)
ap.add_argument('--out', default='/mnt/data2/lab/prof_debordement_double.pt')
ap.add_argument('--device', default='cuda:0')
a = ap.parse_args()

f = MANOEUVRES[a.prof]
O, A = [], []
n_arr = 0; n_tot = 0
for p in range(a.paquets):
    m = fabrique(episodes=a.envs, D=8, seed=5000 + p, device=a.device, steps=a.pas,
                 mode_budget=True, B_min=0.6, B_max=2.5)
    obs = m.reset()
    lot_o, lot_a = [], []
    for t in range(a.pas):
        act = f(m.env, t)
        lot_o.append(obs.clone()); lot_a.append(act.clone())
        obs, _, _, _ = m.step(act, auto_reset=False)
    # on ne garde que les environnements qui ARRIVENT
    garde = m.arrive
    n_arr += int(garde.sum()); n_tot += m.N
    if bool(garde.any()):
        idx = garde.nonzero(as_tuple=False).squeeze(-1)
        O.append(torch.stack(lot_o)[:, idx].reshape(-1, m.obs_dim).cpu())
        A.append(torch.stack(lot_a)[:, idx].reshape(-1).cpu())
    print('  paquet %2d : %d envs arrives sur %d' % (p, int(garde.sum()), m.N), flush=True)

O = torch.cat(O); A = torch.cat(A)
torch.save({'obs': O, 'act': A, 'prof': a.prof}, a.out)
print('')
print('  professeur      : %s' % a.prof)
print('  arrivee         : %.1f%%' % (100.0 * n_arr / n_tot))
print('  paires gardees  : %d' % O.shape[0])
print('  -> %s' % a.out)
print('COLLECTE_DONE')
