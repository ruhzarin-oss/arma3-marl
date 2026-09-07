#!/bin/bash
# Lance par la tache HMT_BOOT apres le montage. Ecrit un compte rendu lisible par machine.
sleep 15
OK=1; MSG=""
mountpoint -q /mnt/data       || { OK=0; MSG="$MSG /mnt/data non monte ;"; }
[ -f /mnt/data/hmt/.temoin ]  || { OK=0; MSG="$MSG temoin absent ;"; }
if [ $OK = 1 ]; then
  # les piles docker (HARMATTAN, Plane) portent restart:always et se relevent seules ; on compte, on ne relance pas
  sleep 60; N=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l); MSG="$MSG conteneurs=$N ;"
  mkdir -p /mnt/data/hmt/etat
  R=/mnt/data/hmt/etat/boot.json
else
  R=/home/younes/boot_ECHEC.json
fi
printf '{"date":"%s","ok":%s,"message":"%s","uptime_s":%s}\n' "$(date -Is)" "$([ $OK = 1 ] && echo true || echo false)" "$MSG" "$(cut -d. -f1 /proc/uptime)" > "$R"
cat "$R"
