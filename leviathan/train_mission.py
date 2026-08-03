#!/usr/bin/env python3
"""train_mission.py — UNE SEULE POLITIQUE POUR DEUX OBJECTIFS CONTRAIRES.

4 agents, monde a objectif parametre (monde_mission.py), verbes PRENDRE et INFILTRER.
Contrat : CONTRAT_ORDRE_DE_MISSION.md (69eadd06ca4122e9).

Reutilise le harnais PPO deja eprouve du projet : Net + ppo_mb de train_koth_gpu.
Rien de neuf cote algorithme — la nouveaute est le MONDE, pas l optimiseur.

L agent recoit son ordre de mission (12 nombres) a chaque pas. La question n est pas
"apprend-il a prendre un objectif" : c est "lit-il son ordre pour changer de conduite".
L audit d ordre (audit_ordre.py) est la seule chose qui repond.
"""
import sys, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from torch.distributions import Categorical
from train_koth_gpu import Net, ppo_mb
from reflexe import CoucheReflexe, N_SEUILS
from monde_mission import fabrique, VERBES

ap = argparse.ArgumentParser()
ap.add_argument('--iters', type=int, default=400)
ap.add_argument('--envs', type=int, default=4096)
ap.add_argument('--rollout', type=int, default=16)
ap.add_argument('--D', type=int, default=8)
ap.add_argument('--lr', type=float, default=3e-4)
ap.add_argument('--hidden', type=int, default=256)
ap.add_argument('--layers', type=int, default=3)
ap.add_argument('--mb', type=int, default=65536)
ap.add_argument('--seed', type=int, default=0)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='/home/younes/arma3-marl/leviathan/mission.pt')
ap.add_argument('--reflexe', action='store_true',
                help='v6 : couche reactive. Le reseau emet les SEUILS de la cascade, pas les gestes. Les deux portes sont franchies : controle nul a zero exact et obeissance sans apprentissage a rho=1,000.')
ap.add_argument('--budget', action='store_true',
                help='monde v5 : l ordre devient un budget de dose, tire log-uniforme')
ap.add_argument('--Bmin', type=float, default=0.6)
ap.add_argument('--Bmax', type=float, default=4.2)
ap.add_argument('--lagrangien', action='store_true',
                help='etape 3b : recompense d ARRIVEE moins lambda fois l exposition, lambda partant de ZERO et monte par ascension duale sur le taux de violation')
ap.add_argument('--cible_violation', type=float, default=0.10)
ap.add_argument('--eta_lambda', type=float, default=0.01)
ap.add_argument('--Bfixe', type=float, default=None,
                help='force le budget a une valeur unique. Bfixe tres grand = budget '
                     'DESACTIVE : c est le controle a un seul changement demande par '
                     'l architecte pour savoir si la machinerie v5 est saine.')
ap.add_argument('--lr_final', type=float, default=0.0,
                help='decroissance lineaire du pas jusqu a cette valeur : un pas '
                     'constant sur une politique durcie est la cause canonique de '
                     'l effondrement tardif observe en v4, 32 pct puis 25,8 pct')
ap.add_argument('--iters_total', type=int, default=None,
                help='budget total declare, pour la decroissance du pas')
ap.add_argument('--iter0', type=int, default=0, help='iteration de depart, pour la reprise')
ap.add_argument('--reprise', default=None,
                help='reprend un point de controle, ETAT DE L OPTIMISEUR COMPRIS : '
                     'sans lui, decouper l entrainement en tranches ne serait plus '
                     'equivalent a un run continu')
a = ap.parse_args()

cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.01)
dev = a.device
m = fabrique(episodes=a.envs, D=a.D, seed=a.seed, device=dev,
             mode_budget=a.budget, B_min=a.Bmin, B_max=a.Bmax,
             budget_force=a.Bfixe)
A, O, NA, N, T = m.A, m.obs_dim, m.n_actions, m.N, a.rollout
net = Net(O, NA + (N_SEUILS if a.reflexe else 0), a.hidden, a.layers).to(dev)
couche = CoucheReflexe(N, A, dev) if a.reflexe else None


def separe(logits):
    """les NA premieres sorties sont les actions, les N_SEUILS suivantes sont les SEUILS.
    Le reseau emet les seuils de la cascade, jamais les gestes — c est la regle d ALIZE."""
    if not a.reflexe:
        return logits, None
    return logits[..., :NA], torch.sigmoid(logits[..., NA:])
opt = torch.optim.Adam(net.parameters(), lr=a.lr)
if a.reprise:
    _ck = torch.load(a.reprise, map_location=dev)
    if isinstance(_ck, dict) and 'net' in _ck:
        net.load_state_dict(_ck['net'])
        # le point de controle du CLONE ne porte que le reseau : pas d optimiseur PPO,
        # il a ete produit par apprentissage supervise. On repart donc d un Adam neuf.
        if 'opt' in _ck:
            opt.load_state_dict(_ck['opt'])
        # LAMBDA DOIT SURVIVRE A LA REPRISE (correctif 2026-07-29). Le runner entrainait par
        # tranches de cent iterations et rechargeait le reseau et l optimiseur, mais PAS le
        # multiplicateur : il repartait de zero toutes les cent iterations et n atteignait
        # jamais la valeur qui fait respecter le budget. Violation mesuree a 84 % pour une
        # cible de 10 %. Meme famille que les autres fautes du jour : un etat qui ne survit
        # pas a la reprise.
        _lam0 = float(_ck.get('lam', 0.0))
        print('  reprise de %s (optimiseur + lambda=%.4f)' % (a.reprise, _lam0), flush=True)
    else:
        net.load_state_dict(_ck)
        _lam0 = 0.0
        print('  reprise de %s (poids seuls)' % a.reprise, flush=True)
m.mode_lagrangien = a.lagrangien
if a.reprise:
    m.lam = _lam0
obs = m.reset()

print('=== ENTRAINEMENT MISSION | %d envs x %d agents | obs %d (dont 12 d ordre) | verbes %s ==='
      % (N, A, O, VERBES), flush=True)
succ = torch.zeros(len(VERBES), device=dev); nb = torch.zeros(len(VERBES), device=dev)
viol_n = torch.zeros((), device=dev); arr_n = torch.zeros((), device=dev)
t0 = time.time(); gstep = 0
for it in range(a.iters):
    B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
             logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
             val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
    for t in range(T):
        with torch.no_grad():
            lg = net.a_logits(obs)
            lg_a, seuils = separe(lg)
            dd = Categorical(logits=lg_a); act = dd.sample()
            # LA COUCHE S APPLIQUE APRES LA POLITIQUE ET PEUT PASSER OUTRE.
            acte = act if couche is None else couche.applique(act, seuils, m)[0]
            # ON CREDITE L ACTION EXECUTEE, JAMAIS L ACTION PROPOSEE (correctif 2026-07-29).
            # La v6 initiale creditait la proposition : la recompense venait pourtant du geste
            # reellement joue apres substitution. L agent apprenait les consequences d actions
            # qu il n avait pas faites — obeissance parfaite, competence exactement nulle sur
            # 400 iterations. Image : le carnet de l eleve enregistrait ce qu il avait voulu
            # faire, pas ce que la voiture a fait.
            B['obs'][t] = obs; B['act'][t] = acte
            B['logp'][t] = dd.log_prob(acte)
            B['val'][t] = net.value(obs)
        obs, rew, fini, info = m.step(acte)
        if couche is not None and bool(fini.any()):
            couche.reset(fini.nonzero(as_tuple=False).squeeze(-1))
        B['rew'][t] = rew; B['done'][t] = fini.float()
        if fini.any():
            for v in range(len(VERBES)):
                sel = fini & (info['verbe'] == v)
                nb[v] += sel.sum(); succ[v] += (sel & info['succes']).sum()
            if a.lagrangien:
                # violation = arrive EN DEPASSANT son budget. C est cette fraction que lambda
                # regule ; il ne monte que si elle depasse la cible.
                arr = fini & info['arrive']
                viol_n += (arr & (info['expo_cum'] > info['Emax'])).sum()
                arr_n += arr.sum()
        gstep += N
    # DECROISSANCE LINEAIRE DU PAS D APPRENTISSAGE sur le budget declare.
    if a.iters_total:
        frac = min(1.0, (a.iter0 + it + 1) / float(a.iters_total))
        for _g in opt.param_groups:
            _g['lr'] = a.lr + (a.lr_final - a.lr) * frac
    with torch.no_grad():
        lv = net.value(obs)
    ppo_mb(net, opt, B, lv, cfg, dev, a.mb)
    if a.lagrangien and float(arr_n) > 0:
        viol = float(viol_n / arr_n)
        m.lam = max(0.0, m.lam + a.eta_lambda * (viol - a.cible_violation))
        if it % 20 == 0:
            print('       lambda %.4f  violation %.1f%%' % (m.lam, 100 * viol), flush=True)
        # PIEGE CONNU : un lambda qui monte trop vite reproduit la penalite fixe, donc
        # l immobilite. Signature d arret pre-enregistree.
        if m.lam > 1.0 and it < 200:
            print('  !! lambda > 1,0 avant l iteration 200 : retour au piege. ARRET.', flush=True)
            break
        viol_n.zero_(); arr_n.zero_()
    if it % 20 == 0 or it == a.iters - 1:
        taux = [100 * (succ[v] / nb[v].clamp(min=1)).item() for v in range(len(VERBES))]
        print('  it %3d | ' % it + ' | '.join('%s %4.1f%% (n=%d)' % (VERBES[v], taux[v], int(nb[v]))
                                              for v in range(len(VERBES)))
              + ' | %.0f tr/s' % (gstep / (time.time() - t0)), flush=True)
        succ.zero_(); nb.zero_()
torch.save({'net': net.state_dict(), 'opt': opt.state_dict(),
            'lam': float(m.lam)}, a.out)
print('-> %s' % a.out, flush=True)
print('TRAIN_MISSION_DONE', flush=True)
