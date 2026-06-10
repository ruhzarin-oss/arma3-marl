#!/bin/bash
cd /home/younes/arma3-marl
echo "=== DISPERSE : M1/M2/M3 x disperse @ skilled, n=16 ==="; date
for m in M1 M2 M3; do
  echo ">>> CELL $m x disperse ..."
  .venv/bin/python -u run_maneuver.py --maneuver $m --geometry disperse --enemy skilled \
      --reps 16 --servers 16 --out "geo_${m}_disperse.jsonl" 2>&1 \
    | grep -E "militaire" | sed "s/^/[$m x disperse] /"
done
echo "=== DISPERSE TERMINEE ==="; date
