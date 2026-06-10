#!/bin/bash
cd /home/younes/arma3-marl
echo "=== PROBE REACT n=8 : M1 vs M3 @ skilled_react (standard) | baseline skilled: M1 50%, M3 62.5% ==="
date
for m in M1 M3; do
  echo ">>> $m skilled_react n=8 ..."
  .venv/bin/python -u run_maneuver.py --maneuver $m --geometry standard --enemy skilled_react \
      --reps 8 --servers 8 --out "react_${m}.jsonl" 2>&1 \
    | grep -E "militaire|=== TABLE|cumul mil" | tail -2 | sed "s/^/[$m react] /"
done
echo "=== PROBE TERMINE ==="
date
