#!/bin/bash
# POINT 3, troisieme tentative : barreau B1i (infiltration).
# Prediction, faite AVANT de jouer : 34 des 51 episodes precedents ARRIVAIENT deja
# (distance mediane au but 1 m) mais ne comptaient pas, faute d'avoir tue le defenseur.
# Avec la condition « arriver vivant », on attend donc ~67 % — DANS la bande 20-80 %
# que Fable exige pour qu'un barreau existe.
cd /home/younes/arma3-marl
exec > point3b.log 2>&1
echo "debut $(date +%H:%M:%S)"
echo "PREDICTION ECRITE D'AVANCE : ~67 % (34/51), bande exigee 20-80 %."
for k in $(seq 1 30); do
  ok=0
  for i in 1 2; do
    R=$(ls -t /mnt/c/Users/Younes/hmtech$i/*.rpt 2>/dev/null | head -1)
    [ -n "$R" ] && grep -q "ETAT PRET" "$R" && ok=$((ok+1))
  done
  [ $ok -eq 2 ] && break
  sleep 10
done
echo ""
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 51 --barreau B1i --capdef \
    --temoins DOCTRINE --sites jugement --dimensionner > p3_b1i_doct.log 2>&1 &
A=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 --barreau B1i --capdef \
    --temoins ALEATOIRE --sites jugement --dimensionner > p3_b1i_alea.log 2>&1 &
B=$!
wait $A; wait $B
echo "  DOCTRINE  : $(grep 'DOCTRINE :' p3_b1i_doct.log)"
echo "  ALEATOIRE : $(grep 'ALEATOIRE :' p3_b1i_alea.log)"
echo "fini $(date +%H:%M:%S)"
