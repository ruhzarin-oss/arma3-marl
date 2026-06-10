#!/bin/bash
cd /home/younes/arma3-marl
echo "=== CONFIRMATION DISPERSE n=32 : M1+M3 seeds 16-31 (append) @ skilled ==="
date
for m in M1 M3; do
  echo ">>> $m disperse seeds 16-31 ..."
  .venv/bin/python -u run_maneuver.py --maneuver $m --geometry disperse --enemy skilled \
      --reps 16 --seed_base 16 --servers 16 --out "geo_${m}_disperse.jsonl" 2>&1 \
    | grep -E "militaire|=== TABLE|cumul mil" | tail -3 | sed "s/^/[$m disperse +16] /"
done
echo "=== CONFIRMATION TERMINEE ==="
date
