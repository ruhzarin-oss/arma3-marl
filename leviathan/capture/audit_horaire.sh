#!/usr/bin/env bash
# audit_horaire.sh — audit partiel du corpus ouvert, une fois par heure.
# La PREMIERE execution est un AUDIT DE MISE EN SERVICE : v2 complete, lecture humaine des
# indicateurs de frontiere avant que les heures suivantes ne comptent comme corpus.
# Un taux au-dela de 3x son seuil met le segment en QUARANTAINE dans meta.json ; la capture
# continue — une heure contaminee est une donnee de diagnostic, pas une raison de perdre la nuit.
set -u
CAP=/home/younes/arma3-marl/leviathan/capture
PY=/home/younes/env_isaaclab/bin/python3
JR=/mnt/data2/lab/replay/openworld/AUDIT_HORAIRE.log
{
  echo "===== $(date -Is) ====="
  for d in /mnt/data2/lab/replay/openworld/inst*/*/; do
    [ -f "$d/state.jsonl" ] || continue
    n=$(wc -l < "$d/state.jsonl")
    [ "$n" -lt 100 ] && continue
    echo "--- $d ($n ticks) ---"
    $PY "$CAP/audit_contamination.py" --session "$d" 2>&1 | grep -E "^  \[|^  monde|^  INDICATEUR|^  vitesse|^VERDICT"
  done
  echo "--- disque ---"
  du -sh /mnt/data2/lab/replay/openworld 2>/dev/null
  df -h /mnt/data2 | tail -1
} >> "$JR" 2>&1
