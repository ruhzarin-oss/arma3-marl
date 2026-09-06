#!/bin/bash
# ⚠️ LE TEMOIN GARDE UNE INSTANCE, PAS UN PROJET. La doctrine n'a jamais tourne sur
# l'instance 2 : une degradation de CETTE instance serait restee invisible, et elle
# expliquerait a elle seule le declin 94 -> 72 de la graine 1.
# On rejoue donc la doctrine SUR LES DEUX instances, apres coup, meme bassin.
cd /home/younes/arma3-marl
exec > controle_instances.log 2>&1
echo "debut $(date +%H:%M:%S) — bande exigee : DOCTRINE >= 97,6 %"
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 51 \
    --temoins DOCTRINE --sites jugement --dimensionner > ci_1.log 2>&1 &
A=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 \
    --temoins DOCTRINE --sites jugement --dimensionner > ci_2.log 2>&1 &
B=$!
wait $A; wait $B
echo ""
echo "instance 1 : $(grep 'DOCTRINE :' ci_1.log)"
echo "instance 2 : $(grep 'DOCTRINE :' ci_2.log)"
echo "fini $(date +%H:%M:%S)"
