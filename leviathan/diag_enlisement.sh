#!/usr/bin/env bash
# diag_enlisement.sh — 22 OPERATIONS SUR 24 SE SONT ENLISEES. POURQUOI ?
# Zero destruction : les attaquants sont VIVANTS, arretes a 40-110 m, jusqu a epuisement
# du budget de pas. Une seule variable testee ici : LE BUDGET DE PAS.
# Si 150 pas convertissent les enlisements en prises ou en destructions, le banc manquait
# simplement de temps. Sinon, c est la logique d assaut qui bloque et il faudra la lire.
# Une variable a la fois : tout le reste est identique au run de certification.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
NAG=12
STEPS="${STEPS:-150}"

echo "=== DIAG ENLISEMENT : memes cellules, budget de pas 60 -> $STEPS ==="
for d in 8 12; do
  for rep in 1 2; do
    out="diag_enl_${d}_${rep}.json"
    echo "--- A=$NAG D=$d frontal rep=$rep steps=$STEPS"
    timeout 180 python3 poser_fob.py "$d" 2>&1 | tail -1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag "$NAG" >/dev/null 2>&1
    timeout 900 python3 envelop_arma.py run --theatre altis --mode frontal --nag "$NAG" \
        --steps "$STEPS" --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out "$out" 2>&1 | tail -1
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done

echo ""
python3 - <<'PY'
import json, glob, re
print(' D  rep  pris  west_fin  dist_min  east_neutralises')
res = []
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/diag_enl_*_*.json')):
    m = re.search(r'diag_enl_(\d+)_(\d+)\.json', f)
    d = json.load(open(f))['metrics']
    res.append((int(m.group(1)), int(m.group(2)), d))
    print(' %2d   %d   %5s    %2d/%2d      %3d m        %d/%d'
          % (int(m.group(1)), int(m.group(2)), d['took'], d['west_end'], d['west_start'],
             d['min_fob_dist'], d['east_neutralized'], d['east_start']))
resolus = sum(1 for _, _, d in res if d['took'] or d['west_end'] == 0)
print('')
print('  resolus (pris OU detruits) : %d/%d' % (resolus, len(res)))
if resolus >= 3:
    print('  >>> LE BANC MANQUAIT DE TEMPS. Le budget de pas devient un parametre du protocole.')
elif resolus == 0:
    print('  >>> LE TEMPS N EST PAS LA CAUSE. Les attaquants sont bloques par autre chose :')
    print('      lire la logique d assaut (assault_tick, standoff) avant tout nouveau run.')
else:
    print('  >>> PARTIEL : le temps aide mais ne suffit pas. Les deux causes coexistent.')
PY
echo "DIAG_DONE"
