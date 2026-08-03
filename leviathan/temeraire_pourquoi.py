#!/usr/bin/env python3
"""temeraire_pourquoi.py — pourquoi l executeur temeraire domine-t-il, et la cible de classement
est-elle degeneree ?

Deux questions posees par l architecte, repondues sur les episodes DEJA collectes (nuit 0 modee).
Aucune nouvelle mesure sur le serveur.

Q1. Le temeraire gagne-t-il par la VITESSE ou parce que le monde sous-punit l exposition ?
    Signature attendue si c est la vitesse : il traverse la zone de detection (100 m mesures) en
    moins de temps, donc il y passe moins de temps-homme, et il perd moins pour la meme distance.
    Signature d un monde qui sous-punit : il passe AUTANT de temps expose et perd quand meme moins.

Q2. La cible de classement est-elle degeneree ? Si le meme executeur est premier aux trois
    rapports de force, un predicteur CONSTANT passe la porte sans rien savoir du monde. On mesure
    la stabilite des classements par bootstrap, comme convenu.
"""
import glob, json, math, os, random
from collections import defaultdict

SORTIE = '/mnt/data2/lab/replay/nuit0'
R_DETECTION = 100.0        # rayon mesure sur Arma le 30/07 : falaise nette
MODES = ['frontal', 'supfront', 'envelop', 'reckless']
random.seed(7)

cas = defaultdict(list)
for f in sorted(glob.glob(os.path.join(SORTIE, 'n0_*.json'))):
    d = json.load(open(f))
    m, meta = d.get('metrics', {}), d.get('_meta', {})
    if m.get('east_start') != 8 or m.get('steps', 0) < 3:
        continue
    fob = d.get('fob')
    frames = d.get('frames', [])
    if not fob or not frames:
        continue
    fx, fy = fob[0], fob[1]
    # temps-homme passe a moins de 100 m de l objectif, et distance parcourue dans cette zone
    th_expose = 0
    d_min = 1e9
    d_debut = None
    pas_dans_zone = 0
    for fr in frames:
        dans = 0
        for w in fr.get('west', []):
            if len(w) < 3 or not w[2]:
                continue
            dd = math.hypot(w[0] - fx, w[1] - fy)
            d_min = min(d_min, dd)
            if d_debut is None:
                d_debut = dd
            if dd < R_DETECTION:
                dans += 1
        th_expose += dans
        if dans:
            pas_dans_zone += 1
    cas[(meta['mode'], meta['A'])].append({
        'pris': bool(m.get('took')), 'pertes': m.get('west_start', 0) - m.get('west_end', 0),
        'A': meta['A'], 'pas': m.get('steps', 0), 'th_expose': th_expose,
        'pas_zone': pas_dans_zone, 'd_min': d_min if d_min < 1e9 else None,
    })

AGS = sorted({A for (_, A) in cas})
print('=== Q1 — LE TEMERAIRE GAGNE-T-IL PAR LA VITESSE ? ===')
print('  (temps-homme expose = somme, sur les pas, du nombre d attaquants vivants a moins de 100 m)')
print()
print('  %-9s %4s %7s %7s %9s %11s %10s' % ('mode', 'A', 'prise', 'pertes', 'pas', 'th_expose', 'th/homme'))
for A in AGS:
    for mode in MODES:
        v = cas.get((mode, A), [])
        if not v:
            continue
        n = len(v)
        pr = sum(1 for e in v if e['pris']) / n
        pe = sum(e['pertes'] for e in v) / n
        pa = sum(e['pas'] for e in v) / n
        th = sum(e['th_expose'] for e in v) / n
        print('  %-9s %4d %6.0f%% %7.2f %9.1f %11.0f %10.1f'
              % (mode, A, 100 * pr, pe, pa, th, th / A))
    print()

print('  --- lecture ---')
for A in AGS:
    t = cas.get(('reckless', A), [])
    f = cas.get(('frontal', A), [])
    if not t or not f:
        continue
    tt = sum(e['th_expose'] for e in t) / len(t) / A
    tf = sum(e['th_expose'] for e in f) / len(f) / A
    pt = sum(e['pertes'] for e in t) / len(t)
    pf = sum(e['pertes'] for e in f) / len(f)
    print('  A=%-2d  temeraire : %.1f pas-homme exposes/homme, %.2f pertes | frontal : %.1f, %.2f'
          % (A, tt, pt, tf, pf))
    if tt < 0.8 * tf and pt < pf:
        print('        -> il est EXPOSE MOINS LONGTEMPS. La vitesse explique la victoire.')
    elif tt >= 0.8 * tf and pt < pf:
        print('        -> il est expose AUTANT et perd MOINS : le monde sous-punit l exposition.')
        print('           C est le jumeau inverse du bac a sable 4x trop letal. A instruire.')
    else:
        print('        -> signature mixte, ne rien conclure.')

print()
print('=== Q2 — LA CIBLE DE CLASSEMENT EST-ELLE DEGENEREE ? ===')
B = 2000
for A in AGS:
    dispo = [m for m in MODES if cas.get((m, A))]
    if len(dispo) < 3:
        continue
    ordres = defaultdict(int)
    premiers = defaultdict(int)
    for _ in range(B):
        moy = []
        for m in dispo:
            v = cas[(m, A)]
            ech = [random.choice(v)['pertes'] for _ in range(len(v))]
            moy.append((sum(ech) / len(ech), m))
        moy.sort()
        ordres[tuple(m for _, m in moy)] += 1
        premiers[moy[0][1]] += 1
    ordre_mod, n_mod = max(ordres.items(), key=lambda kv: kv[1])
    prem_mod, np_mod = max(premiers.items(), key=lambda kv: kv[1])
    print('  A=%-2d  classement modal %-52s stable %5.1f %%'
          % (A, ' < '.join(ordre_mod), 100.0 * n_mod / B))
    print('        premier modal %-10s stable %5.1f %%' % (prem_mod, 100.0 * np_mod / B))
    print('        -> classement complet %s pour la porte (seuil 80 %%)'
          % ('RETENU' if n_mod >= 0.8 * B else 'ECARTE'))

prem = []
for A in AGS:
    v = [(sum(e['pertes'] for e in cas[(m, A)]) / len(cas[(m, A)]), m) for m in MODES if cas.get((m, A))]
    if v:
        prem.append(min(v)[1])
print()
print('  premiers par rapport de force : %s' % prem)
if len(set(prem)) == 1:
    print('  >>> CIBLE DEGENEREE sur le top-1 : un predicteur CONSTANT passerait « premier aux trois')
    print('      rapports » sans rien savoir du monde. La porte doit garder le Spearman sur les')
    print('      classements COMPLETS : toute l information est dans l ordre des perdants.')
else:
    print('  >>> le top-1 change avec le rapport de force : la cible n est pas degeneree.')
print('TEMERAIRE_DONE')
