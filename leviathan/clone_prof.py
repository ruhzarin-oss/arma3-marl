#!/usr/bin/env python3
"""clone_prof.py — clonage du professeur, puis PORTE 4a de l architecte.

Porte 4a, pre-enregistree : accord d action top-1 >= 70 % sur des donnees tenues a l ecart,
ET arrivee de l eleve clone >= 77 % (0,8 x professeur).

Piege a verifier : le professeur ne lit AUCUNE observation, son action depend d un etat cache
(phase de crochet, cote assigne, temps). L eleve ne peut pas cloner ce qu il ne voit pas. Un
accord proche du hasard (11 % pour 9 canaux utiles) signifie observation aliasee.
"""
import sys, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch, torch.nn as nn
from train_koth_gpu import Net

ap = argparse.ArgumentParser()
ap.add_argument('--donnees', default='/mnt/data2/lab/prof_debordement_double.pt')
ap.add_argument('--epoques', type=int, default=3)
ap.add_argument('--lot', type=int, default=16384)
ap.add_argument('--lr', type=float, default=1e-3)
ap.add_argument('--hidden', type=int, default=256)
ap.add_argument('--layers', type=int, default=3)
ap.add_argument('--out', default='/home/younes/arma3-marl/leviathan/ckpt/clone.pt')
ap.add_argument('--device', default='cuda:0')
a = ap.parse_args()

d = torch.load(a.donnees, map_location='cpu')
O, A = d['obs'], d['act']
n = O.shape[0]
# 5 % TENUS A L ECART : l accord se mesure sur des donnees jamais vues a l entrainement
n_test = n // 20
perm = torch.randperm(n, generator=torch.Generator().manual_seed(7))
i_test, i_tr = perm[:n_test], perm[n_test:]
print('  paires : %d entrainement, %d tenues a l ecart' % (len(i_tr), len(i_test)), flush=True)

net = Net(O.shape[1], 13, a.hidden, a.layers).to(a.device)
opt = torch.optim.Adam(net.parameters(), lr=a.lr)
perte = nn.CrossEntropyLoss()

for ep in range(a.epoques):
    ordre = i_tr[torch.randperm(len(i_tr))]
    tot = 0.0; nb = 0
    for k in range(0, len(ordre) - a.lot, a.lot):
        idx = ordre[k:k + a.lot]
        o = O[idx].to(a.device); y = A[idx].to(a.device)
        l = perte(net.a_logits(o), y)
        opt.zero_grad(); l.backward(); opt.step()
        tot += float(l); nb += 1
    with torch.no_grad():
        bons = 0
        for k in range(0, len(i_test), a.lot):
            idx = i_test[k:k + a.lot]
            o = O[idx].to(a.device); y = A[idx].to(a.device)
            bons += int((net.a_logits(o).argmax(-1) == y).sum())
        acc = 100.0 * bons / len(i_test)
    print('  epoque %d : perte %.4f | accord tenu a l ecart %.1f%%' % (ep, tot / max(nb, 1), acc), flush=True)

import os
os.makedirs(os.path.dirname(a.out), exist_ok=True)
torch.save({'net': net.state_dict()}, a.out)
print('')
print('=== PORTE 4a (accord >= 70 %%) ===')
print('  accord top-1 tenu a l ecart : %.1f%%' % acc)
if acc >= 70.0:
    print('  >>> CLONABLE. Reste a verifier l arrivee de l eleve, seuil 77 %%.')
elif acc < 20.0:
    print('  >>> ACCORD PROCHE DU HASARD : le professeur depend d un etat cache que l eleve')
    print('      ne voit pas — phase de crochet, cote assigne, temps. Observation aliasee.')
else:
    print('  >>> ACCORD INSUFFISANT (%.1f%% < 70 %%). Le professeur n est pas imitable depuis' % acc)
    print('      cette observation telle quelle.')
print('-> %s' % a.out)
print('CLONE_DONE')
