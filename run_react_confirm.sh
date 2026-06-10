#!/bin/bash
cd /home/younes/arma3-marl
echo "=== CONFIRM REACT n=16 : M1+M3 @ skilled_react seeds 8-15 (append) ==="
date
for m in M1 M3; do
  echo ">>> $m skilled_react seeds 8-15 ..."
  .venv/bin/python -u run_maneuver.py --maneuver $m --geometry standard --enemy skilled_react \
      --reps 8 --seed_base 8 --servers 8 --out "react_${m}.jsonl" 2>&1 \
    | grep -E "militaire|=== TABLE" | tail -2 | sed "s/^/[$m react +8] /"
done
echo "=== CONFIRM TERMINE ==="
date
