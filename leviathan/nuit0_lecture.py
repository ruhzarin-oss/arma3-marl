#!/usr/bin/env python3
"""nuit0_lecture.py — LECTURE de la nuit 0. Ne collecte rien, ne corrige rien.

Criteres : CRITERES_NUIT0.md (4745631a705e79c0). Refuse de lire si le fichier a bouge.

Separation stricte collecte / jugement : la collecte a ecrit des episodes bruts, la lecture
recalcule tout depuis les ingredients. En particulier le predicat de succes est RECONSTRUIT
(objectif pris) et confronte au champ 'took' ecrit par le collecteur ; toute divergence arrete
le programme. Ce controle a attrape trois de mes propres bugs le 29/07.
"""
import glob, hashlib, json, math, os, sys
from collections import defaultdict

LEV = '/home/younes/arma3-marl/leviathan'
SORTIE = '/mnt/data2/lab/replay/nuit0'
CRIT = os.path.join(LEV, 'CRITERES_NUIT0.md')
ATTENDU = '4745631a705e79c0'
MODES = ['frontal', 'supfront', 'envelop', 'reckless']

emp = hashlib.sha256(open(CRIT, 'rb').read()).hexdigest()[:16]
if emp != ATTENDU:
    sys.exit('REFUS : criteres modifies (%s au lieu de %s).' % (emp, ATTENDU))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


cases = defaultdict(list)
rejets = defaultdict(int)
divergences = []

for f in sorted(glob.glob(os.path.join(SORTIE, 'n0_*.json'))):
    try:
        d = json.load(open(f))
    except Exception:
        rejets['illisible'] += 1
        continue
    m = d.get('metrics', {})
    meta = d.get('_meta', {})
    mode, A = meta.get('mode'), meta.get('A')
    if mode is None or A is None:
        rejets['sans_meta'] += 1
        continue
    # --- controles de validite, pre-enregistres. Un episode qui les rate est REJETE, pas moyenne.
    if m.get('east_start') != 8:
        rejets['defense_incomplete'] += 1
        continue
    if m.get('west_start') != A:
        rejets['attaque_incomplete'] += 1
        continue
    if m.get('steps', 0) < 3:
        rejets['episode_vide'] += 1
        continue
    # --- RECALCUL du predicat : l objectif est pris si un attaquant vivant a franchi le rayon
    #     de securisation. On le reconstruit depuis took_tick, et on le confronte a 'took'.
    recalcule = m.get('took_tick') is not None
    if bool(recalcule) != bool(m.get('took')):
        divergences.append((os.path.basename(f), m.get('took'), m.get('took_tick')))
    pertes = (m.get('west_start', A) - m.get('west_end', 0))
    cases[(mode, A)].append({
        'pris': bool(m.get('took')), 'pertes': pertes,
        'neutralises': m.get('east_neutralized', 0), 'dmin': m.get('min_fob_dist'),
        'pas': m.get('steps', 0), 'instance': meta.get('instance'),
    })

if divergences:
    print('DIVERGENCE de predicat sur %d episode(s) :' % len(divergences))
    for n, t, tt in divergences[:5]:
        print('   %s : took=%s took_tick=%s' % (n, t, tt))
    sys.exit(4)

AGS = sorted({A for (_, A) in cases})
total = sum(len(v) for v in cases.values())
print('=== NUIT 0 — LECTURE (criteres 4745631a705e79c0) ===')
print('  episodes retenus : %d' % total)
if rejets:
    print('  REJETES : %s' % ', '.join('%s=%d' % kv for kv in sorted(rejets.items())))
else:
    print('  aucun rejet')
print()

print('--- (1) OU LE SUCCES APPARAIT ---')
print('  %-10s %s' % ('mode', ''.join('  A=%-2d  succes      Wilson' % A for A in AGS)))
source = []
for mode in MODES:
    ligne = '  %-10s' % mode
    for A in AGS:
        v = cases.get((mode, A), [])
        k, n = sum(1 for e in v if e['pris']), len(v)
        b, h = wilson(k, n)
        ligne += '  %2d/%-2d  %4.0f%%  [%2.0f;%2.0f]' % (k, n, 100.0 * k / n if n else 0, 100 * b, 100 * h)
        if n and k >= 5:
            source.append((mode, A, k, n))
    print(ligne)
print()
if source:
    print('  SOURCE DE SUCCES trouvee : %s' % ', '.join('%s a A=%d (%d/%d)' % s for s in source))
    print('  -> le plan continue : le corpus contiendra des issues positives.')
else:
    print('  AUCUNE case avec >= 5 succes sur 20.')
    print('  -> on ne bricole pas. La tache est peut-etre infaisable a cette geometrie ;')
    print('     c est un arbitrage de CADRAGE qui remonte au chercheur.')
print()

print('--- (2) ORDRE DES MANOEUVRES par pertes attaquant, LU PAR RAPPORT DE FORCE ---')
print('  (jamais en moyenne sur les A : deux rapports peuvent bouger en sens contraire et s annuler)')
for A in AGS:
    l = []
    for mode in MODES:
        v = cases.get((mode, A), [])
        if v:
            l.append((sum(e['pertes'] for e in v) / len(v), mode))
    l.sort()
    print('  A=%-2d  %s' % (A, '  <  '.join('%s (%.2f)' % (m, p) for p, m in l)))
print()

print('--- (3) VARIANCE, pour calibrer la largeur des futurs intervalles ---')
pf = max(cases.items(), key=lambda kv: (sum(1 for e in kv[1] if e['pris']), len(kv[1])))
(mode, A), v = pf
mu = sum(e['pertes'] for e in v) / len(v)
sd = (sum((e['pertes'] - mu) ** 2 for e in v) / max(len(v) - 1, 1)) ** 0.5
print('  case la plus fournie en succes : %s a A=%d (n=%d)' % (mode, A, len(v)))
print('  pertes : moyenne %.2f  ecart-type %.2f  -> demi-largeur a 95%% ~ %.2f' % (mu, sd, 1.96 * sd / len(v) ** 0.5))
print()

print('--- controle par instance (une instance deux fois moins productive est suspecte) ---')
par = defaultdict(int)
for v in cases.values():
    for e in v:
        par[e['instance']] += 1
med = sorted(par.values())[len(par) // 2] if par else 0
susp = [i for i, n in par.items() if n < med / 2]
print('  mediane %d episodes/instance ; suspectes : %s' % (med, susp if susp else 'aucune'))
print('NUIT0_LECTURE_DONE')
