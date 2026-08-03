#!/usr/bin/env bash
# eclaireur_fibua.sh — ECLAIREUR, PAS CERTIFICATION.
#
# But : trouver le regime ou Arma SEPARE les doctrines. On repere, on ne certifie pas ;
# la certification (gros n, criteres haches) se lance apres relecture humaine.
#
# CONTRAINTE ABSOLUE : chaque case fait apparaitre SA PROPRE garnison par script
# (`poser_fob.py`). Le banc ne depend plus jamais d'une garnison de mission — mesure du
# 27/07 : le serveur Stratis redemarre avec ZERO unite EAST, la garnison meurt avec lui.
#
# Grille : rapport de forces x appui
#   8 contre 8   sans appui (frontal)  et  avec fixeurs (envelop)
#  12 contre 8   sans appui (frontal)  et  avec fixeurs (envelop)
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
NAGS="${NAGS:-8 12}"
MODES="${MODES:-frontal envelop}"
REPS="${REPS:-6}"
STEPS="${STEPS:-60}"

for rep in $(seq 1 "$REPS"); do
  for nag in $NAGS; do
    for mode in $MODES; do
      out="${PREF:-ecl}_${nag}_${mode}_${rep}.json"
      echo "=== nag=$nag mode=$mode rep=$rep -> $out  ($(date '+%H:%M'))"
      timeout 120 python3 ${POSEUR:-poser_fob.py} 8 || { echo "  garnison non posee — case sautee"; continue; }
      timeout 180 python3 envelop_arma.py setup --theatre stratis --nag "$nag" >/dev/null 2>&1
      timeout 300 python3 envelop_arma.py run --theatre stratis --mode "$mode" --nag "$nag" \
          --steps "$STEPS" --offset 45 --standoff 70 --flank ${FLANK:-0.45} --assault_tick 24 \
          --out "$out" 2>&1 | tail -2
      timeout 120 python3 envelop_arma.py disarm --theatre stratis >/dev/null 2>&1
    done
  done
done
echo "ECLAIREUR_DONE"
