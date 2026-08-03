#!/usr/bin/env bash
# debit_ferme.sh — mesure le DEBIT reel de la ferme : un episode sur chacune des M instances,
# tous en meme temps. On lit le temps de mur, pas la somme des temps : c est le parallelisme
# qu on mesure, contention comprise.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
M=${1:-14}
A=${2:-4}
T0=$(date +%s)
for i in $(seq 0 $((M-1))); do
  (
    TH=ferme$i
    export HMT_THEATRE=$TH
    t=$(date +%s)
    timeout 180 python3 poser_fob.py 8 >/dev/null 2>&1
    timeout 180 python3 envelop_arma.py setup --theatre $TH --nag $A >/dev/null 2>&1
    timeout 600 python3 envelop_arma.py run --theatre $TH --mode envelop --nag $A \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out debit_$TH.json >/dev/null 2>&1
    timeout 150 python3 envelop_arma.py disarm --theatre $TH >/dev/null 2>&1
    echo "  $TH : $(( $(date +%s) - t )) s"
  ) &
done
wait
MUR=$(( $(date +%s) - T0 ))
echo "MUR $M episodes en parallele : $MUR s"
/home/younes/env_isaaclab/bin/python3 - "$M" "$MUR" <<'PY'
import json, sys, glob
M, mur = int(sys.argv[1]), int(sys.argv[2])
ok = pas = pris = 0
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/debit_ferme*.json')):
    try:
        d = json.load(open(f)); m = d['metrics']
    except Exception:
        continue
    ok += 1; pas += m.get('steps', 0); pris += 1 if m.get('took') else 0
print('  episodes valides : %d / %d' % (ok, M))
print('  pas de decision collectes : %d' % pas)
print('  objectif pris : %d' % pris)
if mur > 0 and ok:
    print('  DEBIT : %.0f episodes/h   %.0f pas/h' % (ok * 3600.0 / mur, pas * 3600.0 / mur))
PY
