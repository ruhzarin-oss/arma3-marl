#!/usr/bin/env bash
# balayage_ratio.sh — le rapport de forces, autour du point FIBUA certifie (23/07).
# Criteres figes AVANT : leviathan/CRITERES_RATIO_FIBUA.md
#
# Une seule variable : le nombre d'attaquants. La garnison est REPOSEE a l'identique avant
# chaque episode (sinon le denominateur bouge tout seul — defaut visible dans les runs
# du 23/07 : east_start 8, 7, 8).
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
NAGS="${NAGS:-8 12 18}"
MODES="${MODES:-frontal supfront envelop}"
REPS="${REPS:-2}"
STEPS="${STEPS:-60}"



for rep in $(seq 1 "$REPS"); do
  for nag in $NAGS; do
    for mode in $MODES; do
      out="ratio_${nag}_${mode}_${rep}.json"
      echo "=== nag=$nag mode=$mode rep=$rep -> $out"
      python3 poser_fob.py 8 || { echo "  garnison non reposee"; continue; }
      python3 envelop_arma.py setup --theatre stratis --nag "$nag" >/dev/null 2>&1
      timeout 300 python3 envelop_arma.py run --theatre stratis --mode "$mode" --nag "$nag" \
          --steps "$STEPS" --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
          --out "$out" 2>&1 | tail -3
      python3 envelop_arma.py disarm --theatre stratis >/dev/null 2>&1
    done
  done
done
echo "BALAYAGE_DONE"
