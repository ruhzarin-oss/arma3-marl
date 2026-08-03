#!/usr/bin/env python3
"""evaluer_boucle_ouverte.py — le modele predit-il SANS qu on lui rende d observation ?

C est la seule lecture qui compte. Un modele auquel on redonne la verite a chaque pas ne predit
rien, il recopie. Ici : on l amorce sur quelques pas observes, puis on coupe le cordon et on le
laisse derouler seul. On mesure l ecart en METRES entre ce qu il imagine et ce qui s est passe.

Trois temoins obligatoires, sinon le chiffre ne veut rien dire :
  - FIGE       : predire que personne ne bouge. Le temoin le plus bete.
  - INERTIE    : prolonger la derniere vitesse observee. Le temoin honnete.
  - le modele.
Un modele qui ne bat pas l inertie n a rien appris.

Usage : evaluer_boucle_ouverte.py --modele m.pt --racine /mnt/data2/lab/replay/banc_essai
"""
import argparse, glob, json, math, os, sys

import torch

sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import monde_rssm as M

ap = argparse.ArgumentParser()
ap.add_argument('--modele', required=True)
ap.add_argument('--racine', default=None, help='defaut : le corpus de banc Arma')
ap.add_argument('--manoeuvre', default=None, help='ne lire que cette manoeuvre (le held-out)')
ap.add_argument('--amorce', type=int, default=10)
ap.add_argument('--deroule', type=int, default=20)
ap.add_argument('--device', default='cuda:0')
a = ap.parse_args()

if a.racine:
    M.NUIT0 = a.racine
dev = a.device
ck = torch.load(a.modele, map_location=dev, weights_only=False)
m = M.RSSM().to(dev)
m.load_state_dict(ck['modele'])
m.eval()

c = M.Corpus(held_out=None, avec_ouvert=False, longueur=a.amorce + a.deroule)
eps = c.banc
if a.manoeuvre:
    keep = []
    for e in eps:
        idx = e['ctx'][:4].argmax().item()
        if M.DOCTRINES[idx] == a.manoeuvre and e['ctx'][:4].sum() > 0:
            keep.append(e)
    eps = keep
if not eps:
    sys.exit('REFUS : aucun episode a evaluer.')
print('=== boucle ouverte : %d episodes | amorce %d pas | deroule %d pas ==='
      % (len(eps), a.amorce, a.deroule))
print('  modele : corpus=%s graine=%s pas=%s held-out=%s'
      % (ck.get('corpus'), ck.get('graine'), ck.get('pas'), ck.get('held_out')))

L = a.amorce + a.deroule
err_m, err_f, err_i, n_fen = 0.0, 0.0, 0.0, 0
par_ep = []
with torch.no_grad():
    for e in eps:
        T = e['obs'].shape[0]
        if T < L + 1:
            continue
        deb = list(range(0, T - L, max(1, a.deroule // 2)))
        em = ef = ei = 0.0
        k = 0
        for d in deb:
            o = e['obs'][d:d + L].unsqueeze(0).to(dev)
            ctx = e['ctx'].unsqueeze(0).to(dev)
            h = torch.zeros(1, m.det, device=dev)
            s = torch.zeros(1, m.sto, device=dev)
            for t in range(a.amorce):                       # amorce : on observe
                s, _, _ = m.observer(o[:, t], ctx, h)
                h = m.avancer(h, s, ctx)
            # ORDRE CRITIQUE. A l entrainement, tetes(h_t, s_t) DECRIT l observation t, et h_t a
            # deja ete avance depuis t-1. En boucle ouverte il faut donc : avancer, tirer le latent
            # depuis la loi A PRIORI (aucune observation), puis decrire. Premiere version fautive :
            # elle decrivait a partir d un latent construit sur l image PRECEDENTE — le modele
            # redecrivait le dernier passe au lieu de predire.
            for t in range(a.amorce, L):                    # deroule : cordon coupe
                s = m.imaginer(h)
                dec, _, _, _ = m.tetes(h, s)
                pred = M.symexp(dec)
                vrai = o[:, t]
                # ecart en METRES sur les attaquants VIVANTS
                pa = pred[:, :M.A_MAX * M.F_ATT].view(1, M.A_MAX, M.F_ATT)
                va = vrai[:, :M.A_MAX * M.F_ATT].view(1, M.A_MAX, M.F_ATT)
                msk = (va[..., 4] > 0.5) & (va[..., 2] > 0.5)
                if msk.any():
                    d2 = ((pa[..., :2] - va[..., :2]) ** 2).sum(-1).sqrt() * M.ECHELLE
                    em += float(d2[msk].mean())
                    # temoin FIGE : la derniere observation de l amorce
                    fa = o[:, a.amorce - 1, :M.A_MAX * M.F_ATT].view(1, M.A_MAX, M.F_ATT)
                    df = ((fa[..., :2] - va[..., :2]) ** 2).sum(-1).sqrt() * M.ECHELLE
                    ef += float(df[msk].mean())
                    # temoin INERTIE : derniere vitesse observee, prolongee
                    p1 = o[:, a.amorce - 1, :M.A_MAX * M.F_ATT].view(1, M.A_MAX, M.F_ATT)
                    p0 = o[:, a.amorce - 2, :M.A_MAX * M.F_ATT].view(1, M.A_MAX, M.F_ATT)
                    ext = p1[..., :2] + (p1[..., :2] - p0[..., :2]) * (t - a.amorce + 1)
                    di = ((ext - va[..., :2]) ** 2).sum(-1).sqrt() * M.ECHELLE
                    ei += float(di[msk].mean())
                    k += 1
                # le modele avance sur SA propre imagination : aucune observation rendue
                h = m.avancer(h, s, ctx)
        if k:
            par_ep.append((em / k, ef / k, ei / k))
            err_m += em; err_f += ef; err_i += ei; n_fen += k

if not n_fen:
    sys.exit('REFUS : aucune fenetre evaluable.')
mm, mf, mi = err_m / n_fen, err_f / n_fen, err_i / n_fen
print()
print('  %-12s %10s' % ('', 'ecart (m)'))
print('  %-12s %10.2f' % ('FIGE', mf))
print('  %-12s %10.2f' % ('INERTIE', mi))
print('  %-12s %10.2f' % ('MODELE', mm))
print()
print('  gain sur le fige    : %+.1f %%' % (100.0 * (mf - mm) / mf))
print('  gain sur l inertie  : %+.1f %%' % (100.0 * (mi - mm) / mi))
print('  episodes : %d | fenetres : %d' % (len(par_ep), n_fen))
print()
if mm < mi and mm < mf:
    print('  >>> le modele bat les deux temoins.')
else:
    print('  >>> LE MODELE NE BAT PAS SES TEMOINS. Il n a rien appris d utile.')
print('EVAL_DONE')
