#!/usr/bin/env python3
"""lire_took.py — LA CONDITION DU REETIQUETAGE : combien d episodes ARRIVENT a l objectif ?

On ne redessine pas une cible autour d une fleche tombee a mi-chemin. Un episode ou
l escouade est detruite ou n arrive jamais n est le succes de personne, et il n y a rien a
reetiqueter. Ce qui compte n est donc pas le taux de SUCCES mais le taux de TOUCHER.

Lecture seule des journaux deja ecrits.
"""
import json, glob, re, collections

LEV = '/home/younes/arma3-marl/leviathan'


def lot(motif):
    par = collections.defaultdict(lambda: [0, 0, 0, 0.0])   # n, took, succes, expo au took
    for f in glob.glob(LEV + '/journaux/' + motif):
        recs = [json.loads(l) for l in open(f)]
        ent = [r for r in recs if r['type'] == 'entete']
        if not ent:
            continue
        e = ent[-1]
        eps = [r for r in recs if r['type'] == 'episode' and r.get('run') == e['run']]
        if not eps:
            continue
        cle = e.get('budget')
        for x in eps:
            a = par[cle]
            a[0] += 1
            if x.get("arrive", x["took"]):
                a[1] += 1
                a[3] += x['expo_au_took']
            if x['succes_monde']:
                a[2] += 1
    return par


print('=== TAUX DE TOUCHER — la matiere premiere du reetiquetage ===')
print('  %-28s %8s %9s %9s %12s' % ('qui', 'budget', 'ARRIVE', 'succes', 'expo au touche'))
for nom, motif in (('agent v6b graine 0', 'evb_v6b_g0_400_b*.jsonl'),
                   ('agent v6b graine 1', 'evb_v6b_g1_400_b*.jsonl'),
                   ('agent v6b graine 2', 'evb_v6b_g2_400_b*.jsonl'),
                   ('doctrine debordement simple', 'front_debordement_simple_b*.jsonl'),
                   ('doctrine frontal', 'front_frontal_delibere_b*.jsonl')):
    par = lot(motif)
    for b in sorted(par, key=lambda x: (x is None, x)):
        n, tk, sc, ex = par[b]
        if n == 0:
            continue
        print('  %-28s %8s %8.1f%% %8.1f%% %12s'
              % (nom, ('%.1f' % b) if b is not None else '-', 100.0 * tk / n, 100.0 * sc / n,
                 ('%.2f' % (ex / tk)) if tk else '-'))
print('')
print('=== LECTURE ===')
par = lot('evb_v6b_g0_400_b*.jsonl')
tot = sum(v[0] for v in par.values()); tk = sum(v[1] for v in par.values())
if tot:
    t = 100.0 * tk / tot
    print('  agent : %.1f %% des episodes atteignent l objectif' % t)
    if t < 5:
        print('  >>> RIEN A REETIQUETER. La fleche n arrive pas sur la cible : le levier ne')
        print('      mordra pas. Il faut d abord apprendre a ARRIVER, budget ou pas.')
    elif t < 30:
        print('  >>> MATIERE MINCE mais reelle. Le reetiquetage donnera %d fois plus' % max(1, int(t / 1))
              + ' d exemples positifs qu aujourd hui.')
    else:
        print('  >>> MATIERE ABONDANTE. Le reetiquetage transforme la quasi-totalite des echecs')
        print('      en exemples reussis ranges par budget.')
print('LIRE_TOOK_DONE')
