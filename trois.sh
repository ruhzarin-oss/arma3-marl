#!/bin/bash
cd /home/younes/arma3-marl
exec > trois.log 2>&1
echo "debut $(date +%H:%M:%S)"
echo "DOCTRINE portee a n=153 : a 49/51 l'estimation n'est plus au plafond, son IC compte."
echo "ALEATOIRE a n=51 comme aux barreaux precedents."
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 153 \
    --temoins DOCTRINE  --sites jugement --dimensionner > d153.log 2>&1 &
A=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 \
    --temoins ALEATOIRE --sites jugement --dimensionner > a51.log 2>&1 &
B=$!
echo "doctrine n=153 pid=$A   ·   aleatoire n=51 pid=$B"
wait $A; wait $B
echo ""; grep -h "DOCTRINE :\|ALEATOIRE :" d153.log a51.log
echo "fini $(date +%H:%M:%S)"
