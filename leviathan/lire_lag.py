#!/usr/bin/env python3
"""lire_lag.py <prefixe> — arrivee, succes et violation. Lecture seule."""
import json, glob, re, sys
nom = sys.argv[1]
LEV = '/home/younes/arma3-marl/leviathan'
out = []
for f in sorted(glob.glob('%s/journaux/%s_b*.jsonl' % (LEV, nom))):
    b = re.search(r'_b([0-9.]+)\.jsonl', f).group(1)
    r = [json.loads(l) for l in open(f)]
    ent = [x for x in r if x['type'] == 'entete']
    if not ent:
        continue
    e = [x for x in r if x['type'] == 'episode' and x.get('run') == ent[-1]['run']]
    if not e:
        continue
    arr = [x for x in e if x.get('arrive')]
    viol = [x for x in arr if x['expo_cum'] > x['Emax']]
    out.append('B=%s arr %5.1f%% succ %5.1f%% viol %5.1f%%'
               % (b, 100.0 * len(arr) / len(e),
                  100.0 * sum(1 for x in e if x['succes_monde']) / len(e),
                  100.0 * len(viol) / max(len(arr), 1)))
if out:
    print('  %-18s %s' % (nom, '   '.join(out)))
