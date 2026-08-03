#!/usr/bin/env bash
# nuit0.sh — enveloppe de file pour la collecte NUIT 0 sur la ferme de 14 serveurs.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
# la ferme doit etre debout AVANT : ce run ne la lance pas, il refuse de tourner a vide.
VIVANTS=$(pgrep -cf "staging/server[0-9]*\.cfg" || true)
if [ "${VIVANTS:-0}" -lt 12 ]; then
  echo "REFUS : seulement ${VIVANTS:-0} instances de ferme debout sur 12. Lancer ferme_lancer.sh 14 d abord."
  exit 3
fi
/home/younes/env_isaaclab/bin/python3 nuit0.py --n 20 --ags 4,8,12 --instances 12
