#!/usr/bin/env python3
"""juge_bilan.py — bilan du professeur chez le juge externe, avec intervalle de Wilson."""
import json, glob, re, collections, math

GYM = 96.2
SEUIL = 86.0


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - m), 100 * (c + m)


par = collections.defaultdict(list)
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/juge_b*_r*.json')):
    b = int(re.search(r'juge_b(\d+)_', f).group(1))
    par[b].append(json.load(open(f))['metrics'])

print('=== LE PROFESSEUR CHEZ LE JUGE — 4 attaquants contre 8 defenseurs ===')
print('  %6s %5s %8s %10s' % ('bloc', 'n', 'pris', 'enlises'))
k = n = 0
taux = []
for b in sorted(par):
    o = par[b]
    kb = sum(1 for x in o if x['took'])
    k += kb; n += len(o)
    taux.append(100.0 * kb / len(o))
    print('  %6d %5d %7.0f%% %9.0f%%' % (b, len(o), 100.0 * kb / len(o),
          100.0 * sum(1 for x in o if not x['took'] and x['west_end'] > 0) / len(o)))
if n == 0:
    print('  aucune operation'); raise SystemExit
lo, hi = wilson(k, n)
print('')
print('  TOTAL : %d pris sur %d = %.1f%%' % (k, n, 100.0 * k / n))
print('  intervalle de Wilson 95 %% : [%.1f%% ; %.1f%%]' % (lo, hi))
if len(taux) > 1:
    print('  etendue inter-blocs : %.0f points (bruit binomial attendu sur n=8 : ~35 points)'
          % (max(taux) - min(taux)))
print('')
print('=== VERDICT (gymnase annonce %.1f%%, seuil %.0f%%) ===' % (GYM, SEUIL))
if lo >= SEUIL:
    print('  >>> GYMNASE CREDIBLE. La manoeuvre rend chez le juge ce que le gymnase annonce.')
elif hi < SEUIL:
    print('  >>> GYMNASE CONDAMNE pour cette configuration. Ecart reel superieur a 10 points,')
    print('      hors bruit. Toute revendication tiree du gymnase est gelee.')
else:
    print('  >>> INDECIS. Doubler a n=80, meme regle.')
