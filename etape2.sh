#!/bin/bash
cd /home/younes/arma3-marl
exec > etape2.log 2>&1
echo "debut $(date +%H:%M:%S)"
./.venv/bin/python -u fuite.py
echo "--- charge longue : doctrine n=1200 sur sites tires, ~4 h ---"
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 1200 \
    --temoins DOCTRINE --sites jugement --dimensionner > fuite_charge.log 2>&1 < /dev/null &
A=$!
echo "charge lancee, pid=$A"
wait $A
echo ""
echo "############ LA JAUGE AU FIL DU RUN ############"
R=$(ls -t /mnt/c/Users/Younes/hmtech2/*.rpt | head -1)
grep "\[ECHP\] JAUGE" "$R" | awk 'NR==1 || NR%15==0' | sed 's/^/  /'
echo ""
grep "DOCTRINE :" fuite_charge.log
echo "fini $(date +%H:%M:%S)"
