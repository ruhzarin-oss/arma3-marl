#!/bin/bash
# Nourrice du pilote P5 : une ssh COURTE par tick ; declenche HMT_RUN tant qu il y a moins de 12 jobs en vol.
CIBLE=12
MUET=0
for i in $(seq 1 400); do
  R=$(ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'wsl -u younes -- bash /mnt/c/Users/Younes/etat_file.sh' 2>/dev/null | tr -d '\r' | grep '^ETAT' | tail -n 1)
  if [ -z "$R" ]; then MUET=$((MUET+1)); echo "$(date +%H:%M:%S) tick $i : ssh muet ($MUET)"; sleep 60; continue; fi
  MUET=0
  set -- $R; EC=$2; AT=$3; LIBRE=$4
  F=$(ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'wsl -u younes -- bash -c "grep -c \"FINI 2026-09-16_PILOTE_P5\" /mnt/data/hmt/etat/file.log; grep -c \"REFUSE 2026-09-16_PILOTE_P5\" /mnt/data/hmt/etat/file.log"' 2>/dev/null | tr -d '\r' | tr '\n' ' ')
  if [ "$AT" -eq 0 ] && [ "$EC" -eq 0 ]; then echo "$(date +%H:%M:%S) tick $i : file vide, rien en vol ( finis refuses : $F) -> arret"; echo ">>> PILOTE FINI"; break; fi
  if [ "$EC" -lt "$CIBLE" ] && [ "$AT" -gt 0 ] && [ "${LIBRE:-0}" -gt 6 ]; then
    ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'schtasks.exe /run /tn HMT_RUN' >/dev/null 2>&1
    echo "$(date +%H:%M:%S) tick $i : vol $EC/$CIBLE attente $AT libre ${LIBRE}Go finis/refuses $F-> +1"
  else
    echo "$(date +%H:%M:%S) tick $i : vol $EC/$CIBLE attente $AT libre ${LIBRE}Go finis/refuses $F-> rien"
  fi
  sleep 30
done
