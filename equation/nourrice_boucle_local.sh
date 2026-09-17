#!/bin/bash
# Nourrice : tant que des jobs attendent dans la file et que moins de 12 sont en vol, declenche HMT_RUN ( 1 par tick de 30 s ).
# L etat est lu par un SCRIPT pose sur la workstation : un $(...) dans la commande ssh serait interprete par PowerShell.
for i in $(seq 1 4800); do
  R=$(perl -e 'alarm 90; exec @ARGV' ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'wsl -u younes -- bash /mnt/c/hmt/tmp/etat_vol.sh' 2>/dev/null | tr -d '\r' | grep '^ETAT' | tail -n 1)
  if [ -z "$R" ]; then echo "$(date +%H:%M:%S) ssh muet"; sleep 60; continue; fi
  set -- $R; EC=$2; AT=$3; ARRET=$4
  if [ "$ARRET" -gt 0 ] && [ "$AT" -eq 0 ]; then echo "$(date +%H:%M:%S) STOP ou FIN et file vide -> arret"; break; fi
  if [ "$AT" -gt 0 ] && [ "$EC" -lt 12 ]; then
    perl -e 'alarm 60; exec @ARGV' ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'schtasks.exe /run /tn HMT_RUN' >/dev/null 2>&1
    echo "$(date +%H:%M:%S) vol $EC attente $AT -> HMT_RUN"
  fi
  sleep 30
done
