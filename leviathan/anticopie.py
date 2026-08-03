#!/usr/bin/env python3
"""anticopie.py — L ELEVE FAIT-IL AUTRE CHOSE QUE COPIER ? (etape 1 de l architecte, bloquante)

Deux mesures, et leur resultat change ce que la certification externe certifie :

  DIVERGENCE ON-POLICY : on deroule l ELEVE, et a chaque pas on demande au professeur ce qu il
  aurait fait DANS CET ETAT. Fraction des pas ou l action gloutonne differe. Seuil 15 %.
    < 15 %  -> l eleve EST le professeur ; certifier le professeur certifie presque l eleve
    >= 15 % -> l eleve fait autre chose ; il exige sa propre certification

  GAIN A CONTRAINTE SERREE : la ou le professeur est structurellement faible. Seuil +15 points.
    sous le seuil -> le recit est << l affinage polit la copie >>, pas << il depasse son maitre >>

Note : la divergence se mesure ON-POLICY, sur les etats que l ELEVE visite. Mesurer sur les
etats du professeur repondrait a une autre question.
"""
import sys, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from monde_mission import fabrique
from manuel import MANOEUVRES
from train_koth_gpu import Net

ap = argparse.ArgumentParser()
ap.add_argument('--poids', nargs='+', required=True)
ap.add_argument('--prof', default='debordement_double')
ap.add_argument('--envs', type=int, default=2048)
ap.add_argument('--pas', type=int, default=80)
ap.add_argument('--graine', type=int, default=2000)
ap.add_argument('--device', default='cuda:0')
a = ap.parse_args()

f = MANOEUVRES[a.prof]
print('=== DIVERGENCE ON-POLICY contre %s (seuil 15 %%) ===' % a.prof)
print('  %-34s %12s %12s' % ('agent', 'divergence', 'pas compares'))
for p in a.poids:
    m = fabrique(episodes=a.envs, D=8, seed=a.graine, device=a.device, steps=a.pas,
                 mode_budget=True, B_min=0.6, B_max=2.5)
    net = Net(m.obs_dim, m.n_actions, 256, 3).to(a.device)
    ck = torch.load(p, map_location=a.device)
    net.load_state_dict(ck['net'] if isinstance(ck, dict) and 'net' in ck else ck)
    net.eval()
    obs = m.reset()
    diff = 0; tot = 0
    with torch.no_grad():
        for t in range(a.pas):
            ae = net.a_logits(obs).argmax(-1)          # l ELEVE, glouton
            ap_ = f(m.env, t)                          # le PROFESSEUR, dans le MEME etat
            viv = m.env._aalive()
            diff += int(((ae != ap_) & viv).sum()); tot += int(viv.sum())
            obs, _, _, _ = m.step(ae, auto_reset=False)
    print('  %-34s %11.1f%% %12d' % (p.split("/")[-1], 100.0 * diff / max(tot, 1), tot))
print('')
print('=== LECTURE ===')
print('  >= 15 %% : l eleve fait autre chose, il exige sa propre certification externe.')
print('  <  15 %% : l eleve EST le professeur, certifier le professeur suffit presque.')
print('ANTICOPIE_DONE')
