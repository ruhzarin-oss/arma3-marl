#!/usr/bin/env bash
# mesure_assaut_final.sh — L ORDRE D ASSAUT FINAL REND-IL LE BANC CAPABLE DE TRANCHER ?
# Criteres : CRITERES_ASSAUT_FINAL.md. Seuil : >=5 operations sur 6 RESOLUES.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
DIST="${DIST:-80}"   # distance de declenchement (m) : la ou le banc s enlise REELLEMENT
rm -f "$LEV"/af_*.json
for mode in frontal envelop; do
  for rep in 1 2 3; do
    echo "--- A=12 D=12 $mode rep=$rep (assaut final ${DIST} m)"
    timeout 180 python3 poser_fob.py 12 2>&1 | tail -1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag 12 >/dev/null 2>&1
    timeout 900 python3 envelop_arma.py run --theatre altis --mode "$mode" --nag 12 \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --assaut_final "$DIST" --out "af_${mode}_${rep}.json" 2>&1 | grep -E "FRANCHISSEMENT|FOB PRIS|ANÉANTIE|==="
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done
echo ""
python3 - <<'PY'
import json, glob, re
print(' mode      rep  pris  survivants  dist_min  EAST neutralises  resolu')
res=[]
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/af_*.json')):
    m=re.search(r'af_(\w+)_(\d)\.json', f); d=json.load(open(f))['metrics']
    r = d['took'] or d['west_end']==0
    res.append(r)
    print(' %-9s  %s   %5s   %2d/%2d       %3d m        %d/%d          %s'
          % (m.group(1), m.group(2), d['took'], d['west_end'], d['west_start'],
             d['min_fob_dist'], d['east_neutralized'], d['east_start'], 'OUI' if r else 'non'))
n=sum(res)
print('')
print('  RESOLUES : %d/%d  (seuil pre-enregistre : >=5/6)' % (n, len(res)))
print('  (le declenchement se lit dans le journal : lignes FRANCHISSEMENT)')
print('  >>> ' + ('L ORDRE D ASSAUT FINAL ENTRE AU PROTOCOLE. Le banc Arma peut de nouveau trancher,'
                  '\n      la certification du seuil de manoeuvre est relancable.'
                  if n >= 5 else
                  'INSUFFISANT. Ne relancer aucune certification avant d avoir compris.'))
print('  (la comparaison frontal/envelop n est PAS mesuree ici : 3 reps ne tranchent rien)')
PY
echo "ASSAUT_DONE"
