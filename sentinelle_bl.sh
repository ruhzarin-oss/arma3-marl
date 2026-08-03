#!/usr/bin/env bash
# sentinelle_bl.sh — veille sur la nuit de capture.
# ⟨le 31/07 une sentinelle a TUÉ la ferme parce que son motif ne correspondait pas au format
#  réel des ticks : elle déclarait morts des serveurs vivants. Ici le motif est vérifié à
#  l'amorçage, et la sentinelle refuse de démarrer s'il ne trouve rien.⟩
set -u
SB=/mnt/data/harmattan-sandbox
LOG=$SB/logs/serverBL.out
JOURNAL=/home/younes/arma3-marl/sentinelle_bl.journal

# amorçage : le motif reconnaît-il quelque chose ?
sleep 60
if ! grep -q "HMT|COUT|noeuds" "$LOG" 2>/dev/null; then
  echo "$(date +%H:%M) AMORÇAGE ÉCHOUÉ : le motif ne reconnaît rien, je ne surveille pas" >> "$JOURNAL"
  exit 1
fi
echo "$(date +%H:%M) sentinelle amorcée, motif validé" >> "$JOURNAL"

DERNIER=""
while true; do
  sleep 300
  VIVANT=$(pgrep -cf "serverBL\.cfg" 2>/dev/null || echo 0)
  ACTUEL=$(grep "HMT|COUT|noeuds" "$LOG" 2>/dev/null | tail -1)
  UNITES=$(echo "$ACTUEL" | grep -o "unites|[0-9]*" | cut -d'|' -f2)
  FPS=$(echo "$ACTUEL" | grep -o "fps|[0-9.]*" | cut -d'|' -f2)
  TAILLE=$(du -m "$LOG" 2>/dev/null | cut -f1)
  LIBRE=$(df -m /mnt/data | tail -1 | awk '{print int($4/1024)}')

  echo "$(date +%H:%M) serveur=$VIVANT unites=${UNITES:-?} fps=${FPS:-?} log=${TAILLE}Mo libre=${LIBRE}Go" >> "$JOURNAL"

  # le serveur est-il mort ?
  if [ "$VIVANT" -eq 0 ]; then
    echo "$(date +%H:%M) SERVEUR MORT — arrêt de la veille, pas de relance aveugle" >> "$JOURNAL"
    exit 2
  fi
  # la capture est-elle muette ? (le compte-rendu de coût tombe toutes les 60 s)
  if [ "$ACTUEL" = "$DERNIER" ]; then
    echo "$(date +%H:%M) CAPTURE MUETTE depuis 5 min — le serveur vit mais n'émet plus" >> "$JOURNAL"
  fi
  DERNIER="$ACTUEL"
  # le disque tient-il ?
  if [ "${LIBRE:-999}" -lt 100 ]; then
    echo "$(date +%H:%M) DISQUE SOUS 100 Go — arrêt préventif de la capture" >> "$JOURNAL"
    exit 3
  fi
done
