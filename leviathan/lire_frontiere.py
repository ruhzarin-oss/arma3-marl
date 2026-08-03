#!/usr/bin/env python3
"""lire_frontiere.py — lecture seule des journaux de la frontiere par budget."""
import json, glob, re, collections

LEV = '/home/younes/arma3-marl/leviathan'
BUDGETS = ['0.6', '0.9', '1.2', '1.6', '2.2', '3.0', '4.2', '6.0']
DOCTRINES = ['frontal_delibere', 'appui_mouvement', 'debordement_simple',
             'debordement_double', 'infiltration', 'bonds_alternes']

t = collections.defaultdict(dict)
for f in glob.glob(LEV + '/journaux/front_*.jsonl'):
    m = re.search(r'front_(.+)_b([0-9.]+)\.jsonl', f)
    if not m:
        continue
    recs = [json.loads(l) for l in open(f)]
    ent = [r for r in recs if r['type'] == 'entete']
    if not ent:
        continue
    run = ent[-1]['run']
    eps = [r for r in recs if r['type'] == 'episode' and r.get('run') == run]
    if eps:
        t[m.group(1)][m.group(2)] = 100.0 * sum(1 for e in eps if e['succes_monde']) / len(eps)

print('=== FRONTIERE PAR BUDGET — taux de reussite atteignable, 1024 episodes par cellule ===')
print('  %-22s' % 'doctrine' + ''.join('%8s' % ('B=' + b) for b in BUDGETS))
print('  ' + '-' * (22 + 8 * len(BUDGETS)))
for d in DOCTRINES:
    if d not in t:
        continue
    print('  %-22s' % d + ''.join('%7.0f%%' % t[d].get(b, float('nan')) for b in BUDGETS))

print('')
print('=== LECTURE : B_min = le plus petit budget ou une solution CONNUE reussit encore ===')
for b in BUDGETS:
    vals = [t[d][b] for d in DOCTRINES if b in t.get(d, {})]
    if not vals:
        continue
    meilleure = max(vals)
    nom = [d for d in DOCTRINES if t.get(d, {}).get(b) == meilleure][0]
    marque = ''
    if meilleure < 20:
        marque = '   <- sous 20 %, on enseignerait l immobilite'
    print('  B=%-5s  meilleure doctrine : %-22s %5.1f%%%s' % (b, nom, meilleure, marque))
print('LIRE_FRONTIERE_DONE')
