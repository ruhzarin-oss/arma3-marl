#!/usr/bin/env python3
"""calib_bilan.py [A|TOUT] [partiel] — bilan de la courbe, avec intervalle de Wilson."""
import json, glob, sys, math

GYM = {4: 94.6, 8: 99.9, 12: 100.0, 18: 100.0, 24: 100.0}
LEV = '/home/younes/arma3-marl/leviathan'


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - m), 100 * (c + m)


def point(A, motif):
    o = [json.load(open(f))['metrics'] for f in glob.glob(motif)]
    if not o:
        return None
    k = sum(1 for x in o if x['took'])
    return k, len(o), wilson(k, len(o)), sum(x['min_fob_dist'] for x in o) / len(o)


arg = sys.argv[1] if len(sys.argv) > 1 else 'TOUT'
if arg != 'TOUT':
    A = int(arg)
    r = point(A, '%s/calib_A%d_*.json' % (LEV, A))
    if r:
        k, n, (lo, hi), dm = r
        marque = ' (partiel)' if len(sys.argv) > 2 else ''
        print('  A=%-3d n=%-3d prise %5.1f%%  Wilson [%4.1f ; %4.1f]  dist min %3.0f m%s'
              % (A, n, 100.0 * k / n, lo, hi, dm, marque), flush=True)
    raise SystemExit

print('')
print('=== COURBE DE CALIBRATION SUR L ISSUE — D=8, debordement ===')
print('  %4s %6s %10s %18s %10s %10s' % ('A', 'n', 'JUGE', 'Wilson 95%', 'GYMNASE', 'ecart'))
accord = None
for A in (4, 8, 12, 18, 24):
    motif = '%s/juge_b*_r*.json' % LEV if A == 4 else '%s/calib_A%d_*.json' % (LEV, A)
    r = point(A, motif)
    if not r:
        print('  %4d %6s %10s' % (A, '-', 'non mesure')); continue
    k, n, (lo, hi), dm = r
    j = 100.0 * k / n; g = GYM[A]
    ec = g - j
    # ecart le plus favorable au gymnase, bornes comprises
    ec_min = max(0.0, g - hi)
    if accord is None and ec_min <= 10.0 and n >= 32:
        accord = A
    print('  %4d %6d %9.1f%% [%5.1f ; %5.1f]%% %9.1f%% %9.1f' % (A, n, j, lo, hi, g, ec))
print('')
print('=== LECTURE (criteres 162338a0f996a435) ===')
if accord is not None:
    print('  >>> POINT D ACCORD : A=%d. Le bac a sable est representatif A PARTIR DE LA.' % accord)
    print('      En dessous, aucune revendication n en sort.')
else:
    print('  >>> AUCUN POINT D ACCORD sur la plage mesuree. Le bac a sable ne represente Arma')
    print('      a aucun rapport de forces teste. Cela condamne bien plus que l agent.')
