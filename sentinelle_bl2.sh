#!/usr/bin/env bash
# sentinelle_bl2.sh — veille sur la nuit de capture. VERSION 2.
#
# La v1 s'est arrêtée seule à 22h37 : elle vérifiait son motif au bout de 60 s alors que le
# serveur met ~90 s à charger ses mods avant le premier compte-rendu. La consigne était bonne
# — refuser de surveiller si le motif ne reconnaît rien — le minuteur était trop court.
#
# ELLE NE TOUCHE À RIEN. Elle lit, elle écrit dans son journal, c'est tout. Aucun pkill,
# aucune relance : un serveur mort est SIGNALÉ, pas relancé à l'aveugle.
# ⟨le 31/07 une sentinelle a tué la ferme en la croyant morte⟩
set -u
LOG=/mnt/data/harmattan-sandbox/logs/serverBL.out
J=/home/younes/arma3-marl/sentinelle_bl.journal

# amorçage patient : jusqu'à 6 minutes, on réessaie
AMORCE=0
for i in $(seq 1 12); do
  sleep 30
  if grep -q "HMT|COUT|noeuds" "$LOG" 2>/dev/null; then AMORCE=1; break; fi
done
if [ "$AMORCE" -eq 0 ]; then
  echo "$(date +%H:%M) AMORÇAGE ÉCHOUÉ après 6 min — je ne surveille pas (rien touché)" >> "$J"
  exit 1
fi
echo "$(date +%H:%M) sentinelle v2 amorcée, motif validé" >> "$J"

DERNIER=""
while true; do
  VIVANT=$(pgrep -cf "serverBL\.cfg" 2>/dev/null || echo 0)
  A=$(grep "HMT|COUT|noeuds" "$LOG" 2>/dev/null | tail -1)
  U=$(echo "$A" | grep -o "unites|[0-9]*" | cut -d'|' -f2)
  F=$(echo "$A" | grep -o "fps|[0-9.]*" | cut -d'|' -f2)
  T=$(du -m "$LOG" 2>/dev/null | cut -f1)
  L=$(df -m /mnt/data | tail -1 | awk '{print int($4/1024)}')

  # NOUVEAU : l'âge du balayage, pour avoir demain la courbe âge / population
  AGE=$(grep "HMT|AGE|" "$LOG" 2>/dev/null | tail -40 \
        | grep -o "[0-9]*,[0-9.]*,[0-9]*,[0-9]*" \
        | awk -F',' '{s+=$2; n++; e+=$4; c+=$3} END {if(n>0) printf "%.1f %d %d", s/n, c, e}')
  set -- $AGE
  AGEMOY="${1:-?}"; CAND="${2:-0}"; ECART="${3:-0}"

  echo "$(date +%H:%M) serveur=$VIVANT unites=${U:-?} fps=${F:-?} age=${AGEMOY}s cand=$CAND ecartes=$ECART log=${T}Mo libre=${L}Go" >> "$J"

  [ "$VIVANT" -eq 0 ] && { echo "$(date +%H:%M) SERVEUR MORT — signalé, rien relancé" >> "$J"; exit 2; }
  [ "$A" = "$DERNIER" ] && echo "$(date +%H:%M) CAPTURE MUETTE depuis 5 min" >> "$J"
  DERNIER="$A"
  [ "${L:-999}" -lt 100 ] && { echo "$(date +%H:%M) DISQUE SOUS 100 Go — signalé" >> "$J"; exit 3; }
  sleep 300
done
