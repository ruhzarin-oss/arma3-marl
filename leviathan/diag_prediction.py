#!/usr/bin/env python3
"""diag_prediction.py — OU exactement le modele casse-t-il ?

On a tourne en rond en raisonnant sur la perte de reconstruction au lieu de la mesurer en metres.
On mesure donc trois choses distinctes, dans la meme unite :

  1. REDECRIRE : l ecart quand le modele a l image SOUS LES YEUX (loi a posteriori). S il rate ca,
     il n a pas la capacite de representer la scene — probleme d architecture.
  2. UN PAS    : l ecart quand il predit le pas suivant sans le voir (loi a priori). S il rate ca,
     il n a pas appris la dynamique — probleme d apprentissage.
  3. VINGT PAS : l ecart quand il deroule seul. S il rate ca seulement, c est la divergence qui
     s accumule — probleme de regime, pas de fond.

Temoin pour chacun : l inertie, c est-a-dire prolonger la derniere vitesse observee.
"""
import argparse, sys

import torch

sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import monde_rssm as M

ap = argparse.ArgumentParser()
ap.add_argument('--modele', required=True)
ap.add_argument('--racine', default=None)
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
L = a.amorce + a.deroule
print('=== ou le modele casse-t-il ? %d episodes ===' % len(eps))


def ecart_m(pred, vrai):
    """ecart moyen en metres sur les attaquants vivants et presents."""
    pa = pred[:, :M.A_MAX * M.F_ATT].view(-1, M.A_MAX, M.F_ATT)
    va = vrai[:, :M.A_MAX * M.F_ATT].view(-1, M.A_MAX, M.F_ATT)
    msk = (va[..., 4] > 0.5) & (va[..., 2] > 0.5)
    if not msk.any():
        return None
    d = ((pa[..., :2] - va[..., :2]) ** 2).sum(-1).sqrt() * M.ECHELLE
    return float(d[msk].mean())


s_red = s_un = s_vg = s_in1 = s_in20 = 0.0
n_red = n_un = n_vg = 0
with torch.no_grad():
    for e in eps[:200]:
        T = e['obs'].shape[0]
        if T < L + 1:
            continue
        for d0 in range(0, T - L, max(1, a.deroule)):
            o = e['obs'][d0:d0 + L].unsqueeze(0).to(dev)
            ctx = e['ctx'].unsqueeze(0).to(dev)
            h = torch.zeros(1, m.det, device=dev)
            s = torch.zeros(1, m.sto, device=dev)
            for t in range(a.amorce):
                s, _, _ = m.observer(o[:, t], ctx, h)
                dec, _, _, _ = m.tetes(h, s)
                if t >= 2:                                # 1. REDECRIRE
                    v = ecart_m(M.symexp(dec), o[:, t])
                    if v is not None:
                        s_red += v; n_red += 1
                h = m.avancer(h, s, ctx)
            # 2. UN PAS : etat avance, latent tire de la loi a priori, on decrit sans voir
            sp = m.imaginer(h)
            dec, _, _, _ = m.tetes(h, sp)
            v = ecart_m(M.symexp(dec), o[:, a.amorce])
            if v is not None:
                s_un += v; n_un += 1
                p1 = o[:, a.amorce - 1]; p0 = o[:, a.amorce - 2]
                s_in1 += ecart_m(p1 + (p1 - p0), o[:, a.amorce]) or 0.0
            # 3. VINGT PAS
            hh, ss = h.clone(), sp
            for t in range(a.amorce, L):
                dec, _, _, _ = m.tetes(hh, ss)
                if t == L - 1:
                    v = ecart_m(M.symexp(dec), o[:, t])
                    if v is not None:
                        s_vg += v; n_vg += 1
                        p1 = o[:, a.amorce - 1]; p0 = o[:, a.amorce - 2]
                        ext = p1 + (p1 - p0) * (t - a.amorce + 1)
                        s_in20 += ecart_m(ext, o[:, t]) or 0.0
                hh = m.avancer(hh, ss, ctx)
                ss = m.imaginer(hh)

print()
print('  %-28s %12s %12s' % ('', 'modele (m)', 'inertie (m)'))
print('  %-28s %12.2f %12s' % ('1. REDECRIRE (image vue)', s_red / max(n_red, 1), '-'))
print('  %-28s %12.2f %12.2f' % ('2. UN PAS a l aveugle', s_un / max(n_un, 1), s_in1 / max(n_un, 1)))
print('  %-28s %12.2f %12.2f' % ('3. VINGT PAS a l aveugle', s_vg / max(n_vg, 1), s_in20 / max(n_vg, 1)))
print()
red = s_red / max(n_red, 1)
un = s_un / max(n_un, 1)
if red > 8.0:
    print('  >>> il ne sait pas REDECRIRE une image qu il voit : probleme d ARCHITECTURE.')
elif un > 3 * (s_in1 / max(n_un, 1)):
    print('  >>> il redecrit mais ne PREDIT pas a un pas : probleme d APPRENTISSAGE.')
else:
    print('  >>> le fond va ; c est le deroule long qui diverge : probleme de REGIME.')
print('DIAG_DONE')
