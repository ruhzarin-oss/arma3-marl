#!/bin/bash
LEV=/home/younes/arma3-marl/leviathan
cd $LEV
for CRAN in 0 1 2 3; do
  pkill -f bissection_selection 2>/dev/null; sleep 2
  bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
  python3 attendre_pont.py altis || { echo "cran $CRAN : pont jamais pret"; continue; }
  sleep 10
  timeout 400 python3 bissection_selection.py --cran $CRAN 2>&1
  echo '------------------------------------------'
done
echo BISSEL_FIN
