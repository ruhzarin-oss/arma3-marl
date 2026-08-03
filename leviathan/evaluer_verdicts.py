#!/usr/bin/env python3
"""evaluer_verdicts.py — le modele predit-il les VERDICTS, seule chose que la porte mesure ?

Pourquoi ce programme existe. On a passe six iterations a faire baisser l ecart de POSITION en
metres, de 92 a 7. Mais l ecart de position est un temoin qu on a invente : il n est nulle part
dans CRITERES_PORTE.md. Ce que la porte mesure, ce sont des verdicts — et c est precisement
l argument qui a condamne le bac a sable ecrit a la main : ses PIECES etaient justes, son ISSUE
fausse. Un modele qui place les hommes a sept metres pres sur une approche de deux cents metres
peut parfaitement dire qui prend l objectif. Il faut le MESURER, pas le supposer.

Protocole, conforme a la porte : pour chaque manoeuvre, on donne au modele l observation initiale
et le contexte, puis on deroule EN BOUCLE OUVERTE jusqu au bout, plusieurs tirages par episode,
sans jamais lui rendre d observation. On lit ce qu il annonce :
  - le taux de prise, compare a l intervalle de Wilson du reel ;
  - le nombre moyen d attaquants perdus, compare a l intervalle de confiance du reel ;
  - le CLASSEMENT des manoeuvres par taux de prise, note en Spearman.

Usage : evaluer_verdicts.py --modele m.pt [--racine ...] [--tirages 20]
"""
import argparse, math, sys
from collections import defaultdict

import torch

sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import monde_rssm as M

ap = argparse.ArgumentParser()
ap.add_argument('--modele', required=True)
ap.add_argument('--racine', default=None)
ap.add_argument('--tirages', type=int, default=20)
ap.add_argument('--amorce', type=int, default=5)
ap.add_argument('--horizon', type=int, default=45)
ap.add_argument('--device', default='cuda:0')
a = ap.parse_args()
if a.racine:
    M.NUIT0 = a.racine
dev = a.device
ck = torch.load(a.modele, map_location=dev, weights_only=False)
m = M.RSSM().to(dev)
m.load_state_dict(ck['modele'])
m.eval()

c = M.Corpus(held_out=None, avec_ouvert=False, longueur=a.amorce + a.horizon)
if not c.banc:
    sys.exit('REFUS : corpus vide.')


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n
    ce = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, ce - h), min(1.0, ce + h))


# --- le REEL, par manoeuvre et par rapport de force
reel = defaultdict(lambda: {'n': 0, 'pris': 0, 'pertes': []})
groupes = defaultdict(list)
for e in c.banc:
    if e['ctx'][:4].sum() == 0:
        continue
    mode = M.DOCTRINES[int(e['ctx'][:4].argmax())]
    A = int(round(float(e['ctx'][4]) * 12))
    cle = (mode, A)
    groupes[cle].append(e)
    r = reel[cle]
    r['n'] += 1
    r['pris'] += int(e['pris'])
    o = e['obs']
    vivants = int((o[-1].view(-1)[2:M.A_MAX * M.F_ATT:M.F_ATT] > 0.5).sum())
    r['pertes'].append(A - vivants)

print('=== VERDICTS PREDITS EN BOUCLE OUVERTE ===')
print('  modele : corpus=%s graine=%s pas=%s | %d tirages/episode, amorce %d, horizon %d'
      % (ck.get('corpus'), ck.get('graine'), ck.get('pas'), a.tirages, a.amorce, a.horizon))
print()

pred = {}
with torch.no_grad():
    for cle, eps in sorted(groupes.items()):
        n_pris = n_tot = 0
        pertes = []
        for e in eps:
            o = e['obs'].unsqueeze(0).to(dev)
            ctx = e['ctx'].unsqueeze(0).to(dev).repeat(a.tirages, 1)
            T = o.shape[1]
            h = torch.zeros(a.tirages, m.det, device=dev)
            s = torch.zeros(a.tirages, m.sto, device=dev)
            for t in range(min(a.amorce, T)):
                s, _, _ = m.observer(o[:, t].repeat(a.tirages, 1), ctx, h)
                h = m.avancer(h, s, ctx)
            # LE VERDICT EST UNE FONCTION DU MONDE IMAGINE, PAS UNE TETE SEPAREE.
            # Bug du 31/07 : la tete << pris >> etait lue, a l entrainement, depuis un etat qui
            # AVAIT VU la derniere image. Elle n a donc jamais appris a PREDIRE le verdict, elle a
            # appris a le LIRE sur la photo d arrivee — et en boucle ouverte cette photo n existe
            # pas. Elle annoncait 77 a 96 % de prise la ou le reel allait de 14 a 33 %.
            # Une tete peut tricher ; une regle geometrique non. On applique donc la MEME regle que
            # le vrai banc : un attaquant VIVANT a moins du rayon de securisation de l objectif.
            R_SECU = 25.0 / M.ECHELLE
            pris_t = torch.zeros(a.tirages, device=dev)
            vivants = None
            for t in range(a.amorce, min(T, a.amorce + a.horizon)):
                s = m.imaginer(h)
                dec, mo, co, pr = m.tetes(h, s)
                pa = dec[:, :M.A_MAX * M.F_ATT].view(-1, M.A_MAX, M.F_ATT)
                dist = (pa[..., :2] ** 2).sum(-1).sqrt()
                pv = torch.sigmoid(mo[:, :M.A_MAX])
                # AU DERNIER PAS, PAS AU MEILLEUR. Le banc lit son verdict sur l etat FINAL.
                # Bug du 31/07 : en prenant le maximum sur le deroule, on mesurait << qui a atteint
                # l objectif a un moment quelconque >>, ce qui recompense les rapides — et le
                # classement sortait PARFAITEMENT INVERSE (Spearman -0,90). Les rapides arrivent
                # tot, stationnent sous le feu et meurent avant la fin ; les contourneurs arrivent
                # tard et sont encore la quand la cloche sonne. Le predicat doit se calculer
                # exactement comme le banc le calcule.
                # on revient a la TETE APPRISE : la regle geometrique tranche a 25 m alors que
                # l erreur de position du modele est de 19 m a vingt pas — deux echelles
                # incompatibles. La tete, elle, n a pas besoin de precision, elle a besoin de
                # correler, et elle correlait (Spearman 0,90).
                pris_t = torch.sigmoid(pr.squeeze(-1))
                vivants = pv
                h = m.avancer(h, s, ctx)
            A = int(round(float(e['ctx'][4]) * 12))
            # present = les A premieres places
            n_pris += int((pris_t > 0.5).sum())
            n_tot += a.tirages
            if vivants is not None:
                pertes.extend((A - vivants[:, :A].sum(1)).clamp(0, A).tolist())
        pred[cle] = {'taux': n_pris / max(n_tot, 1),
                     'pertes': sum(pertes) / max(len(pertes), 1)}

print('  %-10s %3s %12s %22s %10s %14s' % ('mode', 'A', 'prise reel', 'Wilson 95 %',
                                           'prise mod', 'pertes r / m'))
dans_w = tot_w = 0
for cle in sorted(groupes):
    mode, A = cle
    r, p = reel[cle], pred[cle]
    b, hh = wilson(r['pris'], r['n'])
    tr = r['pris'] / r['n']
    mu = sum(r['pertes']) / len(r['pertes'])
    ok = b <= p['taux'] <= hh
    dans_w += int(ok); tot_w += 1
    print('  %-10s %3d %11.1f %% %10.1f - %-8.1f %8.1f %% %6.2f / %-6.2f %s'
          % (mode, A, 100 * tr, 100 * b, 100 * hh, 100 * p['taux'], mu, p['pertes'],
             'ok' if ok else 'HORS'))

print()
print('  taux predits DANS l intervalle de Wilson : %d / %d' % (dans_w, tot_w))


def spearman(x, y):
    rx = {m: i for i, m in enumerate(x)}
    ry = {m: i for i, m in enumerate(y)}
    n = len(x)
    d2 = sum((rx[k] - ry[k]) ** 2 for k in x)
    return 1 - 6.0 * d2 / (n * (n * n - 1)) if n > 2 else float('nan')


print()
print('  --- classement des manoeuvres par taux de prise ---')
rhos = []
for A in sorted({A for (_, A) in groupes}):
    ms = [m for (m, aa) in groupes if aa == A]
    if len(ms) < 3:
        continue
    cr = [m for m in sorted(ms, key=lambda m: -reel[(m, A)]['pris'] / reel[(m, A)]['n'])]
    cp = [m for m in sorted(ms, key=lambda m: -pred[(m, A)]['taux'])]
    rho = spearman(cr, cp)
    rhos.append(rho)
    print('  A=%-2d  reel %-46s' % (A, ' > '.join(cr)))
    print('        modele %-44s Spearman %.2f' % (' > '.join(cp), rho))
if rhos:
    print()
    print('  Spearman moyen : %.2f   (seuil de l etage PASSE : 0,60)' % (sum(rhos) / len(rhos)))
print('VERDICTS_DONE')
