#!/bin/bash
# ═══ LA PORTE, EN LOTS ═════════════════════════════════════════════════════════════════
# ⚠️ ANGLE MORT DECOUVERT LE 17/08 : le pont meurt en service apres 20-40 min (defaut connu,
# `pont-arma-meurt-en-service`). Une porte de 50 tirages sur UN serveur dure ~1 h et se termine
# en « TROIS TIRAGES SANS REPONSE » — le garde-fou a bien tenu, mais aucun verdict n'est rendu.
# On decoupe donc en LOTS de 12, serveur neuf a chaque lot : cinq lots font 60 tirages, assez
# pour 50 receptions. Chaque lot dure ~15 min, sous la duree de vie du pont.
# ⚠️ Angle mort du decoupage, declare : cinq serveurs au lieu d'un, donc un residu propre au
# serveur reste possible — mais il est desormais REPARTI sur cinq naissances au lieu d'une.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/porte; mkdir -p $D; : > $D/JOURNAL.txt
{ echo "socle : $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)"
  echo "commit: $(git rev-parse --short HEAD)"; } | tee -a $D/JOURNAL.txt
for lot in 1 2 3 4 5; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
  echo "lot $lot  $(date +%H:%M:%S)" | tee -a $D/JOURNAL.txt
  HMT_SESSION="_L$lot" timeout 1200 ./.venv/bin/python -u prevol.py 12 natif 45 > $D/lot$lot.txt 2>&1
  echo "  → $(grep -a '── 12 tirages' $D/lot$lot.txt | head -1)" | tee -a $D/JOURNAL.txt
  echo "    T5=$(grep -ac 'T5 IMMOBILE' $D/lot$lot.txt)  T7=$(grep -ac 'T7 LE CANAL' $D/lot$lot.txt)  muet=$(grep -ac 'SANS REPONSE' $D/lot$lot.txt)" | tee -a $D/JOURNAL.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ PORTE EN LOTS TERMINEE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
