#!/bin/bash
# run_ab3.sh — A/B ARMA À 3 BRAS (Fable) : isole SUPPRESSION vs GÉOMÉTRIE de flanc.
#   A=frontal (simple) | B=supfront (fixeurs + assaut FRONTAL) | C=envelop (fixeurs + FLANC)
# Balaye la défense (6/8/10, skill 0.5), N répétitions, reset propre entre chaque run. Effectif WEST identique partout.
# PRÉREQUIS : canari VERT (Younes connecté, IA active). Lance : bash run_ab3.sh [reps]
cd /home/younes/arma3-marl/leviathan
PY=/home/younes/arma3-marl/.venv/bin/python
NAG=12; STEPS=50; REPS=${1:-3}; SKILL=0.5
echo "=== A/B 3 BRAS | WEST=$NAG | défense skill=$SKILL | reps=$REPS ==="
for N in 6 8 10; do
  for MODE in frontal supfront envelop; do
    for R in $(seq 1 $REPS); do
      $PY spawn_hard_east.py --n $N --skill $SKILL >/dev/null 2>&1; sleep 2
      $PY envelop_arma.py setup --nag $NAG >/dev/null 2>&1; sleep 1
      echo ">>> N=$N MODE=$MODE rep=$R"
      $PY envelop_arma.py run --mode $MODE --nag $NAG --steps $STEPS --out ab3_${N}_${MODE}_${R}.json 2>&1 | grep -E '===|PRIS|ANÉANTIE'
    done
  done
done
echo "AB3_ALL_DONE"
