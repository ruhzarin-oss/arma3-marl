#!/bin/bash
cd /home/younes/arma3-marl
exec > deux.log 2>&1
echo "debut $(date +%H:%M:%S) — on attend que les deux instances soient pretes"
for k in $(seq 1 40); do
  ok=0
  for i in 1 2; do
    R=$(ls -t /mnt/c/Users/Younes/hmtech$i/*.rpt 2>/dev/null | head -1)
    [ -n "$R" ] && grep -q "ETAT PRET" "$R" && ok=$((ok+1))
  done
  [ $ok -eq 2 ] && break
  sleep 10
done
echo "les deux instances repondent PRET a $(date +%H:%M:%S)"
echo ""
echo "SHA de la mission deployee :"
./.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from harnais import sha_mission; print('  ', sha_mission())"

./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 51 \
    --temoins DOCTRINE > regression.log 2>&1 &
A=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 \
    --temoins DOCTRINE --sites jugement --dimensionner > doct_sites.log 2>&1 &
B=$!
echo "regression (site gele) pid=$A   ·   dimensionnement (sites tires) pid=$B"
wait $A; wait $B
echo ""
echo "############ NON-REGRESSION : le monde certifie est-il intact ? ############"
cat regression.log
echo "############ DIMENSIONNEMENT : la doctrine sur sites tires ############"
cat doct_sites.log
echo "fini $(date +%H:%M:%S)"
