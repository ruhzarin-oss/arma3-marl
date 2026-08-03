#!/usr/bin/env python3
"""sonde_verbe.py — LE RESEAU SE SERT-IL DE L ORDRE QU IL VOIT ?

Sonde demandee par l architecte. Elle ne produit AUCUN taux de succes : elle regarde,
sur LES MEMES ETATS, ce que le reseau fait quand on ne change que le verbe affiche.

Deux grandeurs, toutes deux appariees — c est ce qui la rend infiniment plus sensible que
l audit par taux de succes, qui valait 1,1 ecart-type :

  VALEUR   : |V(s, prendre) - V(s, infiltrer)|. Si c est zero, le critique voit le verbe
             mais ne s en sert pas. Alors les retours structurellement plus bas sous
             INFILTRER ne sont absorbes par personne, et la normalisation globale des
             avantages les transforme en penalite sur TOUTE action sous ce verbe.

  ACTIONS  : divergence de Jensen-Shannon entre les deux distributions d actions. Zero
             signifie que la politique joue rigoureusement la meme chose.

Diagnostic, pas mesure : aucun chiffre d ici ne se compare a un etalon.
"""
import sys, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from monde_mission import fabrique, DIM_ORDRE, N_VERBES

ap = argparse.ArgumentParser()
ap.add_argument('--poids', required=True)
ap.add_argument('--envs', type=int, default=2048)
ap.add_argument('--pas', type=int, default=40)
ap.add_argument('--graine', type=int, default=3000)
ap.add_argument('--hidden', type=int, default=256)
ap.add_argument('--layers', type=int, default=3)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--budget', action='store_true',
                help='monde v5 : compare DEUX BUDGETS sur les memes etats. En mode budget les quatre premieres colonnes de l ordre portent le budget et la dose, pas un drapeau de verbe : basculer un one-hot y fabrique des entrees absurdes.')
ap.add_argument('--Blo', type=float, default=0.8)
ap.add_argument('--Bhi', type=float, default=3.5)
a = ap.parse_args()

from train_koth_gpu import Net
m = fabrique(episodes=a.envs, D=8, seed=a.graine, device=a.device, steps=80,
             mode_budget=a.budget, B_min=0.6, B_max=4.2)
net = Net(m.obs_dim, m.n_actions, a.hidden, a.layers).to(a.device)
_ck = torch.load(a.poids, map_location=a.device)
net.load_state_dict(_ck['net'] if isinstance(_ck, dict) and 'net' in _ck else _ck)
net.eval()

obs = m.reset()
dv, djs, n = 0.0, 0.0, 0


def avec_verbe(o, v):
    """le MEME etat, seul le verbe affiche change"""
    o = o.clone()
    o[..., -DIM_ORDRE:-DIM_ORDRE + N_VERBES] = 0.0
    o[..., -DIM_ORDRE + v] = 1.0
    return o


def avec_budget(valeur):
    """le MEME etat du monde, reconstruit avec un autre budget. On passe par le monde et non
    par un bricolage de colonnes : le budget touche a la fois B, la dose relative et le
    budget restant, qui doivent rester coherents entre eux."""
    garde = m.Emax.clone()
    m.Emax = torch.full_like(m.Emax, float(valeur))
    o = m._obs(m.env._obs())
    m.Emax = garde
    return o


with torch.no_grad():
    for t in range(a.pas):
        if a.budget:
            op, oi = avec_budget(a.Bhi), avec_budget(a.Blo)
        else:
            op, oi = avec_verbe(obs, 0), avec_verbe(obs, 1)
        vp, vi = net.value(op), net.value(oi)
        dv += float((vp - vi).abs().mean()); n += 1
        pp = torch.softmax(net.a_logits(op), dim=-1)
        pi = torch.softmax(net.a_logits(oi), dim=-1)
        mm = 0.5 * (pp + pi)
        kl = lambda p, q: (p * (torch.log(p + 1e-12) - torch.log(q + 1e-12))).sum(-1)
        djs += float((0.5 * kl(pp, mm) + 0.5 * kl(pi, mm)).mean())
        acts = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
        obs, _, _, _ = m.step(acts)

print('=== SONDE %s — %s ===' % ('BUDGET %.1f contre %.1f' % (a.Bhi, a.Blo) if a.budget
                                 else 'VERBE', a.poids.split('/')[-1]))
print('  ecart de VALEUR moyen  |V(prendre) - V(infiltrer)| : %.5f' % (dv / n))
print('  divergence des ACTIONS (Jensen-Shannon, 0 = identique) : %.6f' % (djs / n))
print('')
print('=== LECTURE ===')
if dv / n < 1e-3:
    print('  >>> LE CRITIQUE NE SE SERT PAS DU VERBE. Il le voit et l ignore.')
    print('      Les retours plus bas sous INFILTRER ne sont absorbes par personne :')
    print('      la normalisation globale des avantages penalise TOUTE action sous ce verbe,')
    print('      quelle qu elle soit. Ce n est pas un signal faible, c est un poison actif.')
else:
    print('  le critique distingue les deux ordres (ecart %.4f).' % (dv / n))
if djs / n < 1e-4:
    print('  >>> LA POLITIQUE JOUE LA MEME CHOSE dans les deux cas. Aucune ecoute.')
else:
    print('  la politique differe selon l ordre (divergence %.5f).' % (djs / n))
print('SONDE_VERBE_DONE')
