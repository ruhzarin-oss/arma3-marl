#!/bin/bash
# dim60 — DIMENSIONNEMENT DU BARREAU B0@60. On mesure les deux temoins ; on ne juge rien.
# Les deux temoins tournent EN PARALLELE, un par instance : c'est le premier usage reel
# de la parallelisation certifiee ce soir. Doctrine sur l'instance 1, aleatoire sur la 0.
cd /home/younes/arma3-marl
exec > dim60.log 2>&1
echo "debut $(date +%H:%M:%S)"
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 60 --n 51 \
    --temoins DOCTRINE  --dimensionner > dim60_doctrine.log 2>&1 &
P1=$!
./.venv/bin/python -u temoins_traversants.py --instance 0 --D 60 --n 51 \
    --temoins ALEATOIRE --dimensionner > dim60_aleatoire.log 2>&1 &
P0=$!
echo "doctrine pid=$P1 sur instance 1   aleatoire pid=$P0 sur instance 0"
wait $P1; wait $P0
echo ""
echo "############ DOCTRINE (instance 1) ############"; cat dim60_doctrine.log
echo "############ ALEATOIRE (instance 0) ############"; cat dim60_aleatoire.log
echo "fini $(date +%H:%M:%S)"
