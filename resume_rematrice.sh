#!/bin/bash
# resume_rematrice.sh — REPREND la re-matrice 72 cellules apres un reboot, en SAUTANT les cellules deja faites (>=16 ops).
# A lancer APRES le reboot VT-x. Refait la flotte + les cellules partielles/manquantes seulement.
cd /home/younes/arma3-marl
SG=$(cat ~/arma3-marl/hmt_step_game.txt 2>/dev/null || echo 2.17)
L=logs_train/rematrice_resume_$(date +%Y%m%d_%H%M).log
ATKS="M1 M2 M3 M5 M8 M9 M10 M11 M12"
DEFS="skilled skilled_react skilled_react_depth skilled_mobile skilled_elastic skilled_herisson skilled_appat skilled_sortie"
{
echo "===== RESUME RE-MATRICE (step_game=$SG) $(date) ====="
N=0; FAITES=0; AFAIRE=0
# 1) reboot flotte (obligatoire apres reboot machine)
echo "--- reboot flotte 16 ---"; (cd /mnt/data/harmattan-sandbox && bash multi_server.sh 16); sleep 100
for MAN in $ATKS; do for DEF in $DEFS; do
  N=$((N+1)); OUT="mxp_${DEF}_${MAN}.jsonl"
  DONE=$(grep -c "\"mil\"" "$OUT" 2>/dev/null || echo 0)
  if [ "$DONE" -ge 16 ]; then FAITES=$((FAITES+1)); continue; fi
  AFAIRE=$((AFAIRE+1))
  [ -f "$OUT" ] && { echo "cellule $N/72 $MAN x $DEF : partielle ($DONE ops) -> purge + refaite"; rm -f "$OUT"; }
  # reboot preventif flotte toutes les 10 cellules REELLEMENT jouees
  if [ $((AFAIRE % 10)) -eq 0 ]; then echo "--- reboot preventif flotte ---"; (cd /mnt/data/harmattan-sandbox && bash multi_server.sh 16); sleep 100; fi
  echo "===== CELLULE $N/72 : $MAN x $DEF ($(date)) ====="
  HMT_SOCKET=1 HMT_STEP_GAME=$SG timeout 28800 .venv/bin/python run_maneuver.py --maneuver "$MAN" --enemy "$DEF" --servers 16 --reps 16 --max_wall 1800 --stall_wall 600 --out "$OUT"
done; done
echo "===== RESUME FINI : $FAITES deja faites, $AFAIRE (re)jouees. REMATRICE FINIE ====="; date
} >> "$L" 2>&1
echo "$L" > /tmp/hmt_last_rematrice
