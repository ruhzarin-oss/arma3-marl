#!/bin/bash
# Programme de nuit — ni Arma ni presence humaine.
# Chaque phase ecrit son resultat au fur et a mesure : une nuit qui rend deux resultats
# sur trois vaut mieux qu'une nuit morte a 2 h du matin.
cd /home/younes/arma3-marl
./.venv/bin/python leviathan/nuit_apprendre.py \
  --graines 3 --rounds 150 --K 8 --ne 1024 --eval 300 \
  --out nuit_apprendre.json > /tmp/nuit.log 2>&1
echo "NUIT_TERMINEE a $(date +%H:%M)" >> /tmp/nuit.log
