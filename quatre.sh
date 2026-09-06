#!/bin/bash
cd /home/younes/arma3-marl
./.venv/bin/python /tmp/ph.py
./.venv/bin/python -m py_compile temoins_traversants.py || exit 1
exec > quatre.log 2>&1
echo "debut $(date +%H:%M:%S) — bassin v2, trajets secs, graine reproductible"
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 153 \
    --temoins DOCTRINE  --sites jugement --dimensionner > d153b.log 2>&1 &
A=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 \
    --temoins ALEATOIRE --sites jugement --dimensionner > a51b.log 2>&1 &
B=$!
echo "doctrine n=153 pid=$A   ·   aleatoire n=51 pid=$B"
wait $A; wait $B
echo ""; grep -h "DOCTRINE :\|ALEATOIRE :" d153b.log a51b.log
echo "fini $(date +%H:%M:%S)"
