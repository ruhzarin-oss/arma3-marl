#!/usr/bin/env python3
"""lire_evb.py <nom_ckpt> [graine] — lecture seule des journaux d evaluation par budget."""
import json, glob, re, sys

nom = sys.argv[1]
g = sys.argv[2] if len(sys.argv) > 2 else '1000'
t = {}
for f in glob.glob('/home/younes/arma3-marl/leviathan/journaux/evb_%s_b*_g%s.jsonl' % (nom, g)):
    b = float(re.search(r'_b([0-9.]+)_', f).group(1))
    r = [json.loads(l) for l in open(f)]
    ent = [x for x in r if x['type'] == 'entete']
    if not ent:
        continue
    run = ent[-1]['run']
    e = [x for x in r if x['type'] == 'episode' and x.get('run') == run]
    if not e:
        continue
    t[b] = (100.0 * sum(1 for x in e if x['succes_monde']) / len(e),
            sum(x['expo_cum'] for x in e) / len(e))
if t:
    print('  %-14s' % nom + ''.join('   B=%.1f %5.1f%% dose %4.2f' % (b, t[b][0], t[b][1])
                                    for b in sorted(t)))
