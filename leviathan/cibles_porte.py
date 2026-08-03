#!/usr/bin/env python3
"""cibles_porte.py — les cibles que le modele du monde devra reproduire, et leur STABILITE.

Un modele qu on juge contre une cible bruitee est juge par un des. On ne retient donc une cible
que si elle survit au reechantillonnage. Regles posees par l architecte, appliquees telles quelles :

  - une cible n entre dans la porte que si son classement est identique dans >= 80 % des
    reechantillonnages bootstrap ;
  - le premier du classement doit CHANGER avec le rapport de force, sinon un predicteur CONSTANT
    passerait la porte sans rien savoir du monde (cible degeneree) ;
  - l information reelle est dans le classement COMPLET, pas dans le seul vainqueur.

Deux grandeurs candidates : le TAUX DE PRISE et les PERTES. On les lit toutes les deux et on dit
laquelle est utilisable, sans en choisir une d avance.
"""
import glob, json, math, os, random
from collections import defaultdict

SORTIE = '/mnt/data2/lab/replay/nuit0'
MODES = ['frontal', 'supfront', 'envelop', 'reckless']
B = 4000
STABLE = 0.80
random.seed(11)

cas = defaultdict(list)
for f in sorted(glob.glob(os.path.join(SORTIE, 'n0_*.json'))):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    m, meta = d.get('metrics', {}), d.get('_meta', {})
    if m.get('east_start') != 8 or m.get('steps', 0) < 3:
        continue
    cas[(meta['mode'], meta['A'])].append(
        {'pris': 1 if m.get('took') else 0,
         'pertes': m.get('west_start', 0) - m.get('west_end', 0)})

AGS = sorted({A for (_, A) in cas})


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def bootstrap(A, cle, croissant):
    """Renvoie (classement modal, stabilite, premier modal, stabilite du premier)."""
    dispo = [m for m in MODES if cas.get((m, A))]
    ordres, prem = defaultdict(int), defaultdict(int)
    for _ in range(B):
        v = []
        for m in dispo:
            e = cas[(m, A)]
            ech = [random.choice(e)[cle] for _ in e]
            mu = sum(ech) / len(ech)
            v.append((mu if croissant else -mu, m))
        v.sort()
        ordres[tuple(x[1] for x in v)] += 1
        prem[v[0][1]] += 1
    o, n = max(ordres.items(), key=lambda kv: kv[1])
    p, np_ = max(prem.items(), key=lambda kv: kv[1])
    return o, n / B, p, np_ / B


print('=== EFFECTIFS ET MESURES ===')
for A in AGS:
    print('  A=%-2d' % A)
    for m in MODES:
        v = cas.get((m, A), [])
        if not v:
            continue
        n = len(v); k = sum(e['pris'] for e in v)
        b, h = wilson(k, n)
        mu = sum(e['pertes'] for e in v) / n
        sd = (sum((e['pertes'] - mu) ** 2 for e in v) / max(n - 1, 1)) ** 0.5
        print('    %-9s n=%-3d prise %3d/%-3d = %5.1f %% [%4.1f ; %4.1f]   pertes %.2f +- %.2f'
              % (m, n, k, n, 100.0 * k / n, 100 * b, 100 * h, mu, 1.96 * sd / n ** 0.5))
print()

retenu = {}
for cle, croissant, nom, sens in (('pris', False, 'TAUX DE PRISE', '>'),
                                  ('pertes', True, 'PERTES', '<')):
    print('=== CLASSEMENT PAR %s ===' % nom)
    prem_par_A = []
    for A in AGS:
        o, st, p, stp = bootstrap(A, cle, croissant)
        prem_par_A.append(p)
        ok = st >= STABLE
        retenu[(nom, A)] = (o, st, ok)
        print('  A=%-2d  %-52s stable %5.1f %%  [%s]'
              % (A, (' %s ' % sens).join(o), 100 * st, 'RETENU' if ok else 'ecarte'))
        print('        premier %-10s stable %5.1f %%' % (p, 100 * stp))
    degenere = len(set(prem_par_A)) == 1
    print('  premiers : %s -> %s' % (prem_par_A, 'DEGENERE' if degenere else 'non degenere'))
    n_ret = sum(1 for A in AGS if retenu[(nom, A)][2])
    print('  %d classement(s) sur %d utilisable(s) pour la porte' % (n_ret, len(AGS)))
    print()

print('=== VERDICT ===')
util = [(nom, A) for (nom, A), (_, _, ok) in retenu.items() if ok]
if not util:
    print('  AUCUNE cible stable. La porte ne peut pas etre pre-enregistree sur ces donnees.')
    print('  Cause a lire dans les effectifs ci-dessus : si l intervalle de chaque manoeuvre')
    print('  recouvre celui de sa voisine, il faut plus de repetitions, pas un autre critere.')
else:
    print('  cibles utilisables : %s' % ', '.join('%s a A=%d' % u for u in util))
    print('  -> ce sont ELLES qui entrent dans le fichier de criteres de la porte, et rien d autre.')
print('CIBLES_DONE')
