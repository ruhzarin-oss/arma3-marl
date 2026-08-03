#!/bin/bash
# On repart de ce qui survit et on ajoute une piece a la fois, CUMULATIVEMENT.
# Serveur neuf avant chaque piece : un pont deja mort fausserait la suivante.
LEV=/home/younes/arma3-marl/leviathan
for PIECE in 1 5 6 7; do
  bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
  for i in $(seq 1 30); do ss -tlnp 2>/dev/null | grep -q 5826 && break; sleep 5; done
  sleep 10
  cd $LEV && python3 sonde_pieces.py --piece $PIECE --duree 60
  echo '-------------------------------------------'
done
echo BISSECTION_TERMINEE
