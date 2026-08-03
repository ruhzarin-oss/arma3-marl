#!/usr/bin/env bash
# variance_banc.sh — COMBIEN LE BANC BOUGE-T-IL TOUT SEUL ?
# UN SEUL bras, 6 blocs independants de 9 operations. Rien ne varie entre les blocs :
# toute difference observee est du BRUIT, par construction.
# Criteres : CRITERES_VARIANCE_BANC.md (3c8cf3bf50b2228c)
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
BLOCS="${BLOCS:-6}"; PAR_BLOC="${PAR_BLOC:-9}"
rm -f "$LEV"/vb_*.json
for bloc in $(seq 1 "$BLOCS"); do
  for rep in $(seq 1 "$PAR_BLOC"); do
    echo "--- bloc=$bloc rep=$rep (frontal bruyant, A=12 vs D=8)"
    timeout 180 python3 poser_fob.py 8 2>&1 | tail -1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag 12 >/dev/null 2>&1
    timeout 900 python3 envelop_arma.py run --theatre altis --mode frontal --nag 12 \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out "vb_${bloc}_${rep}.json" 2>&1 | grep -E "FOB PRIS|ANÉANTIE|==="
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done
echo ""
python3 - <<'PY'
import json, glob, re, collections, statistics
agg=collections.defaultdict(list)
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/vb_*.json')):
    m=re.search(r'vb_(\d+)_(\d+)\.json', f)
    agg[int(m.group(1))].append(json.load(open(f))['metrics'])
print(' bloc  ops  prise  enlises')
pr=[]
for b in sorted(agg):
    o=agg[b]; n=len(o); p=sum(1 for x in o if x['took'])/n
    pr.append(100*p)
    print('  %2d   %3d   %4.0f%%   %4.0f%%' % (b, n, 100*p,
          100*sum(1 for x in o if not x['took'] and x['west_end']>0)/n))
et = max(pr)-min(pr); sd = statistics.stdev(pr) if len(pr)>1 else 0.0
print('')
print('  ETENDUE (meilleur - pire bloc) : %.0f points' % et)
print('  ecart-type entre blocs         : %.1f points' % sd)
print('')
print('=== LECTURE (criteres figes 3c8cf3bf50b2228c) ===')
if et <= 20:
    print('  >>> BANC UTILISABLE a n=9 par bras (etendue %.0f <= 20).' % et)
    print('      Les A/B passes restent discutables mais pas condamnes.')
elif et <= 40:
    print('  >>> IL FAUT >=30 OPERATIONS PAR BRAS pour lire un effet de 20 points (etendue %.0f).' % et)
    print('      Tout A/B de ce banc fait a moins de 30 ops/bras est NON CONCLUANT,')
    print('      retroactivement, FIBUA du 23/07 compris.')
else:
    print('  >>> LE BANC NE PEUT PAS TRANCHER UN A/B DE DOCTRINE (etendue %.0f > 40).' % et)
    print('      Reduire la variance a la source AVANT toute remesure :')
    print('      garnison figee, meteo figee, spawn fige, monde ALiVE gele.')
PY
echo "VARIANCE_DONE"
