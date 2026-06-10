#!/bin/bash
cd /home/younes/arma3-marl
echo "=== TABLE GEOMETRIE : M1/M2/M3 x {faible_ouest,faible_est,standard} @ skilled, n=16 ==="
date
for g in faible_ouest faible_est standard; do
  for m in M1 M2 M3; do
    echo ">>> CELL $m x $g (n=16) ..."
    .venv/bin/python -u run_maneuver.py --maneuver $m --geometry $g --enemy skilled \
        --reps 16 --servers 16 --out "geo_${m}_${g}.jsonl" 2>&1 \
      | grep -E "militaire|TABLE %|=== TABLE" | sed "s/^/[$m x $g] /"
  done
done
echo "=== TABLE TERMINEE ==="
date
