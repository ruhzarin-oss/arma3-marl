#!/usr/bin/env bash
# enchainer_banc4.sh — attend que le banc n°3 ecrive TERMINE, puis lance le n°4.
# Ne decide rien : le garde-fou est dans lancer_banc4.sh, pas ici.
# Pour annuler : pkill -f enchainer_banc4.sh
set -u
LOGS=/mnt/data/harmattan-sandbox/logs
J="$LOGS/serverBA.out"
CHAINE="$LOGS/enchainement_banc4.log"
LIMITE=$(( 3 * 3600 ))   # au-dela, le banc n°3 est repute plante : on n enchaine PAS

echo "$(date -Is) attente de HMT|ESC3|TERMINE" >> "$CHAINE"
t0=$SECONDS
while true; do
  if grep -q "HMT|ESC3|TERMINE" "$J" 2>/dev/null; then
    echo "$(date -Is) banc n°3 termine, bascule" >> "$CHAINE"
    /home/younes/arma3-marl/lancer_banc4.sh >> "$CHAINE" 2>&1
    echo "$(date -Is) lancer_banc4.sh code $?" >> "$CHAINE"
    exit 0
  fi
  if ! pgrep -x arma3server_x64 >/dev/null; then
    echo "$(date -Is) ABANDON : le serveur est mort avant TERMINE. Rien n a ete lance." >> "$CHAINE"
    exit 2
  fi
  if (( SECONDS - t0 > LIMITE )); then
    echo "$(date -Is) ABANDON : 3 h sans TERMINE, le banc n°3 est repute plante." >> "$CHAINE"
    exit 3
  fi
  sleep 30
done
