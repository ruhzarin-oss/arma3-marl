#!/usr/bin/env bash
# replication_silence.sh — REPLICATION DIMENSIONNEE : 3 bras x 18 operations.
# Criteres : CRITERES_SILENCE_REPLICATION.md (e289a5f5e592ec36)
# Primaire   : prise(frontal silencieux) - prise(frontal bruyant) >= +20 pts
# Secondaire : prise(envelop) - prise(frontal silencieux) <= +10 pts => l avantage du flanc
#              sur ce banc est un ARTEFACT DE L ORDRE DE FEU.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
REPS="${REPS:-18}"
rm -f "$LEV"/rs_*.json
for bras in frontal_bruyant frontal_silencieux envelop_bruyant; do
  case "$bras" in
    frontal_bruyant)    MODE=frontal; SIL="" ;;
    frontal_silencieux) MODE=frontal; SIL="--silencieux" ;;
    envelop_bruyant)    MODE=envelop; SIL="" ;;
  esac
  for rep in $(seq 1 "$REPS"); do
    echo "--- $bras rep=$rep"
    timeout 180 python3 poser_fob.py 8 2>&1 | tail -1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag 12 >/dev/null 2>&1
    timeout 900 python3 envelop_arma.py run --theatre altis --mode "$MODE" --nag 12 \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        $SIL --out "rs_${bras}_${rep}.json" 2>&1 | grep -E "FOB PRIS|ANÉANTIE|==="
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done
echo ""
python3 - <<'PY'
import json, glob, re, collections
agg=collections.defaultdict(list)
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/rs_*.json')):
    m=re.search(r'rs_(\w+?)_(\d+)\.json', f)
    agg[m.group(1)].append(json.load(open(f))['metrics'])
st={}
print(' bras                 ops  prise  enlises  pertes/prise')
for b in ('frontal_bruyant','frontal_silencieux','envelop_bruyant'):
    o=agg.get(b,[])
    if not o: continue
    n=len(o); pris=[x for x in o if x['took']]
    enl=[x for x in o if not x['took'] and x['west_end']>0]
    cout=(sum(x['west_losses'] for x in pris)/len(pris)) if pris else float('nan')
    st[b]={'prise':len(pris)/n,'enl':len(enl)/n,'cout':cout,'n':n}
    print(' %-20s %3d  %4.0f%%   %4.0f%%      %s'
          % (b,n,100*len(pris)/n,100*len(enl)/n,('%.2f'%cout) if cout==cout else '  -  '))
print('')
print('=== LECTURE (criteres figes e289a5f5e592ec36) ===')
hs=[b for b in st if st[b]['enl']>0.40]
if hs:
    print('  >>> BRAS NON MESURE (plus de 40%% d enlisements) : %s'%hs)
else:
    d1=100*(st['frontal_silencieux']['prise']-st['frontal_bruyant']['prise'])
    print('  PRIMAIRE   silencieux - bruyant = %+.0f pts (seuil +20)'%d1)
    if d1>=20:
        print('    >>> CONFIRME : c est l ORDRE DE FEU qui figeait le frontal.')
        d2=100*(st['envelop_bruyant']['prise']-st['frontal_silencieux']['prise'])
        print('  SECONDAIRE envelop - silencieux = %+.0f pts (seuil +10)'%d2)
        if d2<=10:
            print('    >>> L AVANTAGE DU FLANC SUR CE BANC EST UN ARTEFACT DE L ORDRE DE FEU.')
            print('        Tous les A/B frontal-vs-debordement sont a relire, FIBUA 23/07 compris.')
        else:
            print('    >>> le flanc garde un avantage PROPRE, au-dela du mecanisme de feu.')
    elif d1>0:
        print('    >>> effet reel mais MINEUR : l ordre de feu n est pas l explication principale.')
    else:
        print('    >>> le pilote etait du bruit. L hypothese tombe.')
PY
echo "REPLICATION_DONE"
