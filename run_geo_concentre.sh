#!/bin/bash
cd /home/younes/arma3-marl
echo "=== TABLE GEOMETRIE CONCENTRE : M1/M2/M3 x concentre @ skilled, n=16 ==="
date
g=concentre
for m in M1 M2 M3; do
  out="geo_${m}_${g}.jsonl"
  have=$( [ -f "$out" ] && wc -l < "$out" || echo 0 )
  if [ "$have" -ge 16 ]; then
    echo ">>> SKIP $m x $g (déjà $have ops)"
    continue
  fi
  echo ">>> CELL $m x $g (n=16) ..."
  .venv/bin/python -u run_maneuver.py --maneuver $m --geometry $g --enemy skilled \
      --reps 16 --servers 16 --out "$out" 2>&1 \
    | grep -E "militaire|TABLE %|=== TABLE" | sed "s/^/[$m x $g] /"
done
echo "=== TABLE CONCENTRE TERMINEE ==="
date
