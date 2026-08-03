#!/usr/bin/env bash
# certif_bande.sh — CERTIFICATION DANS LA BANDE : A=12 vs D=8, frontal contre envelop.
# Criteres : CRITERES_CERTIF_BANDE.md. Ordre d assaut final DESACTIVE (la bande a ete
# mesuree sans lui). 6 reps par bras.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
rm -f "$LEV"/cb_*.json
for mode in frontal envelop; do
  for rep in 1 2 3 4 5 6; do
    echo "--- A=12 D=8 $mode rep=$rep"
    timeout 180 python3 poser_fob.py 8 2>&1 | tail -1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag 12 >/dev/null 2>&1
    timeout 900 python3 envelop_arma.py run --theatre altis --mode "$mode" --nag 12 \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out "cb_${mode}_${rep}.json" 2>&1 | grep -E "FOB PRIS|ANÉANTIE|===" 
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done
echo ""
python3 - <<'PY'
import json, glob, re, collections
agg=collections.defaultdict(list)
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/cb_*.json')):
    m=re.search(r'cb_(\w+)_(\d)\.json', f)
    agg[m.group(1)].append(json.load(open(f))['metrics'])
print(' mode      ops  prise  abandons  pertes/prise  EAST neutralises')
st={}
for mode in ('frontal','envelop'):
    o=agg[mode]; n=len(o)
    pris=[x for x in o if x['took']]
    aband=[x for x in o if not x['took'] and x['west_end']>0]
    ppp=(sum(x['west_losses'] for x in pris)/len(pris)) if pris else float('nan')
    st[mode]={'prise':len(pris)/n,'aband':len(aband)/n,'cout':ppp}
    print(' %-9s %3d  %4.0f%%    %4.0f%%       %s        %.1f/%d'
          % (mode,n,100*len(pris)/n,100*len(aband)/n,
             ('%.2f'%ppp) if ppp==ppp else '  -  ',
             sum(x['east_neutralized'] for x in o)/n, o[0]['east_start']))
print('')
print('=== LECTURE (criteres figes) ===')
fr=st['frontal']
if not (0.25<=fr['prise']<=0.75):
    print('  >>> HORS BANDE (prise frontale %.0f%%) : cellule NON MESUREE, rien ne se lit.'%(100*fr['prise']))
elif fr['aband']>0.25 or st['envelop']['aband']>0.25:
    print('  >>> TROP D ABANDONS (frontal %.0f%%, envelop %.0f%%) : bras NON MESURE.'
          %(100*fr['aband'],100*st['envelop']['aband']))
else:
    rp=st['envelop']['prise']/fr['prise'] if fr['prise'] else float('inf')
    rc=st['envelop']['cout']/fr['cout'] if fr['cout']==fr['cout'] and fr['cout'] else float('nan')
    print('  dans la bande. prise envelop/frontal x%.2f | cout x%.2f'%(rp,rc))
    print('  PRISE   : %s'%('>>> PREDICTION DU SANDBOX REFUTEE : le flanc achete la prise a D/A=0,67'
                            if rp>=1.5 else 'prediction tenue : le flanc n achete pas la prise ici'))
    if rc==rc:
        print('  COUT    : %s'%('prediction tenue : le flanc achete des vies (x%.2f <= 0,60)'%rc
                                if rc<=0.60 else 'prediction DEMENTIE : le flanc ne reduit pas le cout (x%.2f)'%rc))
PY
echo "CERTIF_BANDE_DONE"
