#!/bin/bash
# ═══ LE TEST DES MÊMES LIEUX — le destin suit-il le lieu ? ═════════════════════════════
# Trouvé en lisant le code : le placeur balaye 24 points FIXES autour d'un homme né une fois
# → le lieu est fixé par session, ce qui est la structure exacte du destin (X² = 56,6).
# Mais la PENTE — seul critère du placeur — ne sépare pas les vivantes des mortes.
#
# CINQ LIEUX ALTERNÉS DANS LA MÊME SESSION, pour éliminer l'effet de session lui-même :
#   morts   4989/5877 · 4716/5207 · 4210/5369      (0 vert sur 6 en ère 1.2)
#   vivants 4776/5196 · 4445/6138                  (6 verts sur 6 en ère 1.2)
#
# SIGNATURES ÉCRITES AVANT — grandeur : taux d'échec T5 par lieu ; statistique : proportion ;
# n minimum : 6 tirages par lieu (2 sessions × 3 passages).
#   (a) LE DESTIN SUIT LE LIEU ... séparation NETTE : le pire lieu vivant échoue MOINS que
#                                  le meilleur lieu mort. → cause établie, placeur fautif.
#   (b) LE LIEU EST UN CORRÉLAT .. pas de séparation ; les lieux d'une même session se
#                                  ressemblent. → DESTIN_EST_LE_LIEU.md TOMBE.
#   (c) INDÉCIS ................. séparation partielle. On ne conclut pas, on ne rejoue pas.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/lieux; mkdir -p $D
{ echo "socle : $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)"
  echo "commit: $(git rev-parse --short HEAD)"; } | tee $D/EMPREINTE.txt
for s in 1 2; do
  if [ -f $D/mes_pids ]; then while read pid; do kill $pid 2>/dev/null; done < $D/mes_pids; fi
  : > $D/mes_pids; sleep 3
  echo "session $s  $(date +%H:%M:%S)" | tee -a $D/JOURNAL.txt
  HMT_SESSION="_L$s" timeout 900 ./.venv/bin/python -u prevol.py 15 lieux 45 > $D/s${s}.txt 2>&1
  pgrep -f arma3server_x64 > $D/mes_pids 2>/dev/null
  echo "  → s$s : $(grep -a '── 15 tirages' $D/s${s}.txt | head -1)" | tee -a $D/JOURNAL.txt
done
if [ -f $D/mes_pids ]; then while read pid; do kill $pid 2>/dev/null; done < $D/mes_pids; fi
echo "═══ TEST DES LIEUX TERMINE — $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
