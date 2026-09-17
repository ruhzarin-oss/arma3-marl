#!/bin/bash
# Nourrice de la boucle EvoGP : tant qu'un job BOUCLE attend dans la file et que moins de 12 jobs sont en vol, declenche HMT_RUN.
# S'arrete si le fichier STOP ou FIN de la boucle existe, ou apres 40 h.
for i in $(seq 1 4800); do
  R=$(perl -e 'alarm 90; exec @ARGV' ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'wsl -u younes -- bash -c "echo ETAT $(ls /mnt/data/hmt/queue/en_cours/ | wc -l) $(ls /mnt/data/hmt/queue/*BOUCLE*.json 2>/dev/null | wc -l) $(ls /mnt/data/hmt/equation/boucle/STOP /mnt/data/hmt/equation/boucle/FIN 2>/dev/null | wc -l)"' 2>/dev/null | tr -d '\r' | grep '^ETAT' | tail -n 1)
  if [ -z "$R" ]; then echo "$(date +%H:%M:%S) ssh muet"; sleep 60; continue; fi
  set -- $R; EC=$2; AT=$3; ARRET=$4
  [ "$ARRET" -gt 0 ] && [ "$AT" -eq 0 ] && { echo "$(date +%H:%M:%S) STOP ou FIN et file vide -> arret"; break; }
  if [ "$AT" -gt 0 ] && [ "$EC" -lt 12 ]; then
    perl -e 'alarm 60; exec @ARGV' ssh -o BatchMode=yes -o ConnectTimeout=25 ws 'schtasks.exe /run /tn HMT_RUN' >/dev/null 2>&1
    echo "$(date +%H:%M:%S) vol $EC attente boucle $AT -> HMT_RUN"
  fi
  sleep 30
done
