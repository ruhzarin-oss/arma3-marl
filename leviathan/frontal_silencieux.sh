#!/usr/bin/env bash
# frontal_silencieux.sh — L AVANTAGE DU FLANC EST-IL UN ARTEFACT DE L ORDRE DE FEU ?
# Une seule variable : --silencieux (fire=0 pour tous en progression). Mode frontal, A=12 vs D=8.
# Criteres : CRITERES_FRONTAL_SILENCIEUX.md
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
rm -f "$LEV"/fs_*.json
for rep in 1 2 3 4 5 6; do
  echo "--- A=12 D=8 frontal SILENCIEUX rep=$rep"
  timeout 180 python3 poser_fob.py 8 2>&1 | tail -1
  timeout 180 python3 envelop_arma.py setup --theatre altis --nag 12 >/dev/null 2>&1
  timeout 900 python3 envelop_arma.py run --theatre altis --mode frontal --nag 12 \
      --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
      --silencieux --out "fs_${rep}.json" 2>&1 | grep -E "FOB PRIS|ANÉANTIE|==="
  timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
done
echo ""
python3 - <<'PY'
import json, glob
o=[json.load(open(f))['metrics'] for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/fs_*.json'))]
n=len(o)
pris=[x for x in o if x['took']]
aband=[x for x in o if not x['took'] and x['west_end']>0]
ta, tp = len(aband)/n, len(pris)/n
print(' FRONTAL SILENCIEUX : %d ops | prise %.0f%% | abandons %.0f%% | dist_min moy %.0f m'
      % (n, 100*tp, 100*ta, sum(x['min_fob_dist'] for x in o)/n))
print(' rappel BRUYANT     : 6 ops | prise 33%% | abandons 67%%')
print(' rappel ENVELOP     : 6 ops | prise 83%% | abandons 17%%')
print('')
print('=== LECTURE (criteres figes) ===')
if ta > 0.25:
    print('  SEUIL 1 ECHOUE (abandons %.0f%% > 25%%) : l ordre de feu n explique PAS l enlisement.'%(100*ta))
    print('  >>> Chercher ailleurs. Rien d autre ne se lit.')
else:
    print('  SEUIL 1 ATTEINT (abandons %.0f%% <= 25%%) : c est bien l ordre de feu qui figeait le frontal.'%(100*ta))
    if tp >= 0.60:
        print('  >>> L AVANTAGE DU FLANC SUR CE BANC EST UN ARTEFACT DE L ORDRE DE FEU.')
        print('      Tous les A/B frontal-vs-debordement de ce banc sont a relire, FIBUA 23/07 compris.')
    elif tp < 0.33:
        print('  >>> LE SILENCE FAIT CHUTER LA PRISE (%.0f%% < 33%%) : tirer en progression coute du'%(100*tp))
        print('      mouvement mais rapporte plus qu il ne coute. A consigner tel quel.')
    else:
        print('  >>> PARTIEL : le silence debloque le mouvement (prise %.0f%%) sans rejoindre l envelop.'%(100*tp))
PY
echo "SILENCE_DONE"
