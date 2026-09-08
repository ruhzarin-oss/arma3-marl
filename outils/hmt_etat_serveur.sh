#!/bin/bash
# Tache HMT_ETAT : regenere l'etat toutes les 10 min et sert /mnt/data/hmt/etat sur 8081.
for i in 1 2 3 4 5 6; do [ -f /mnt/data/hmt/.temoin ] && break; sleep 30; done
cd /mnt/data/hmt/etat || exit 1
python3 -m http.server 8081 --bind 0.0.0.0 >/dev/null 2>&1 &
while true; do python3 /mnt/data/hmt/depot/outils/etat.py >/dev/null 2>&1; bash /mnt/data/hmt/depot/outils/wiki.sh >/dev/null 2>&1; sleep 600; done
