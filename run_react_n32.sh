#!/bin/bash
cd /home/younes/arma3-marl
echo "=== REACT n=32 : M1+M3 @ skilled_react seeds 16-31 (append) ==="
date
for m in M1 M3; do
  echo ">>> $m seeds 16-31 ..."
  .venv/bin/python -u run_maneuver.py --maneuver $m --geometry standard --enemy skilled_react \
      --reps 16 --seed_base 16 --servers 16 --out "react_${m}.jsonl" 2>&1 \
    | grep -E "militaire|=== TABLE" | tail -2 | sed "s/^/[$m +16] /"
done
echo "=== REACT_N32 TERMINE ==="; date
