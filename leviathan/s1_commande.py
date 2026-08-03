#!/usr/bin/env python3
"""s1_commande.py — L ORDRE COMMANDE CONTRE L ORDRE EXECUTE (etape S1, gratuit).

Le banc juge commande aux fixeurs de tenir a `--standoff 70` metres et d y RESTER ; les
crocheteurs, eux, assaillent l objectif. Si les crocheteurs meurent, les survivants sont les
fixeurs, a 70 m — et la << distance d arret >> mesuree est alors un ORDRE, pas un symptome.

Ce que l ecart-type tranche :
    sous 10 m  -> barriere geometrique, donc commandee
    30 m et +  -> attrition, donc subie
"""
import json, glob, statistics, collections

for motif, nom in (('juge_b*_r*.json', 'A=4'), ('calib_A8_*.json', 'A=8'),
                   ('calib_A12_*.json', 'A=12'), ('calib_A24_*.json', 'A=24')):
    o = [json.load(open(f))['metrics'] for f in glob.glob(motif)]
    if not o:
        continue
    d = [x['min_fob_dist'] for x in o]
    et = statistics.pstdev(d) if len(d) > 1 else 0.0
    print('  %-5s n=%-3d  dist min : mediane %3.0f m  ecart-type %4.1f m  [%3.0f ; %3.0f]'
          % (nom, len(o), statistics.median(d), et, min(d), max(d)))
    print('         survivants mediane %.0f sur %d | pris %d'
          % (statistics.median([x['west_end'] for x in o]), o[0]['west_start'],
             sum(1 for x in o if x['took'])))
    ann = collections.Counter()
    for x in o:
        for r in x.get('rings', []):
            if r['west']:
                ann[r['ring']] += r['west']
    if ann:
        print('         morts par anneau : ' + '  '.join('%dm:%d' % (k, v) for k, v in sorted(ann.items())))
    print('         verdict : %s' % ('BARRIERE COMMANDEE (ecart-type < 10 m)' if et < 10
                                     else ('ATTRITION (ecart-type >= 30 m)' if et >= 30
                                           else 'MIXTE (ecart-type entre 10 et 30 m)')))
    print()
