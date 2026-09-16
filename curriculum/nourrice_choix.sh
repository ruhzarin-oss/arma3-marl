#!/bin/bash
# Nourrice des campagnes de choix : une ssh courte par tick ; HMT_RUN tant qu il y a moins de 12 jobs en vol.
# ( HMT_RUN se declenche aussi seul toutes les 10 min : la nourrice ne fait qu accelerer. )
CIBLE=12
for i in $(seq 1 2000); do
  R=$(ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'wsl -u younes -- bash /mnt/c/Users/Younes/etat_file.sh' 2>/dev/null | tr -d '\r' | grep '^ETAT' | tail -n 1)
  if [ -z "$R" ]; then echo "$(date +%H:%M:%S) tick $i : ssh muet"; sleep 60; continue; fi
  set -- $R; EC=$2; AT=$3; LIBRE=$4
  if [ "$AT" -eq 0 ] && [ "$EC" -eq 0 ]; then echo "$(date +%H:%M:%S) file vide, rien en vol -> arret"; echo ">>> CHOIX FINIS"; break; fi
  if [ "$EC" -lt "$CIBLE" ] && [ "$AT" -gt 0 ] && [ "${LIBRE:-0}" -gt 6 ]; then
    ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'schtasks.exe /run /tn HMT_RUN' >/dev/null 2>&1
    echo "$(date +%H:%M:%S) tick $i : vol $EC attente $AT -> +1"
  fi
  sleep 30
done
