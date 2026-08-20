#!/bin/bash
# ═══ LA PORTE, EN LOTS ═════════════════════════════════════════════════════════════════
# ⚠️ ANGLE MORT DECOUVERT LE 17/08 : le pont meurt en service apres 20-40 min (defaut connu,
# `pont-arma-meurt-en-service`). Une porte de 50 tirages sur UN serveur dure ~1 h et se termine
# en « TROIS TIRAGES SANS REPONSE » — le garde-fou a bien tenu, mais aucun verdict n'est rendu.
# On decoupe donc en LOTS de 12, serveur neuf a chaque lot : cinq lots font 60 tirages, assez
# pour 50 tirages mesures. ⚠️ Depuis la fusion du 20/08, un tirage coute ~60-85 s (T5 joue
# jusqu a 8 azimuts) : un lot dure ~16-18 min, encore sous la duree de vie du pont, mais la
# marge s est reduite — c est le garde-fou des trois sans-reponse qui protege desormais.
# ⚠️ Angle mort du decoupage, declare : cinq serveurs au lieu d'un, donc un residu propre au
# serveur reste possible — mais il est desormais REPARTI sur cinq naissances au lieu d'une.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/porte; mkdir -p $D; : > $D/JOURNAL.txt
{ echo "socle : $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)"
  echo "commit: $(git rev-parse --short HEAD)"; } | tee -a $D/JOURNAL.txt
for lot in 1 2 3 4 5; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
  echo "lot $lot  $(date +%H:%M:%S)" | tee -a $D/JOURNAL.txt
  # ⚠️ MINUTEUR DERIVE DU COUT REEL DU MECANISME, ET JAMAIS CONTRAIGNANT ⟨Fable⟩.
  # `timeout 1200` etait un chiffre ROND : le 19/08 il a tronque les cinq lots a 5-7
  # tirages sur 12, en silence, et la porte a ete lue comme si elle avait fini.
  # Derivation : echauffement 45 s + pont/socle/scene ~20 s + 12 tirages a la BORNE
  # EXTERIEURE du prevol (180 s, sa duree maximale legitime) = 45+20+2160 = 2225 s.
  # Arrondi SUPERIEUR a 2400 s. Ce minuteur ne doit JAMAIS mordre : ce sont les gardes
  # nommees (figement, borne exterieure, trois sans-reponse) qui coupent et qui DISENT
  # pourquoi. Un minuteur qui coupe est une panne muette.
  HMT_SESSION="_L$lot" timeout 2400 ./.venv/bin/python -u prevol.py 12 natif 45 > $D/lot$lot.txt 2>&1
  rc=$?; [ "$rc" = "124" ] && echo "  ⛔ LE MINUTEUR A MORDU — lot $lot tronque, le verdict est SANS OBJET" | tee -a $D/JOURNAL.txt
  echo "  → $(grep -a '── 12 tirages' $D/lot$lot.txt | head -1)" | tee -a $D/JOURNAL.txt
  echo "    T5=$(grep -ac 'T5 CANAL MORT' $D/lot$lot.txt)  T7=$(grep -ac 'T7 LE CANAL' $D/lot$lot.txt)  muet=$(grep -ac 'SANS REPONSE' $D/lot$lot.txt)" | tee -a $D/JOURNAL.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ PORTE EN LOTS TERMINEE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
