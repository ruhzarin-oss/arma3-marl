#!/bin/bash
# Lance la courbe n1. PASSER PAR CE SCRIPT et pas par une commande ssh directe :
# un pkill -f dont le motif figure dans sa propre ligne de commande se tue lui-meme
# (arrive 2x le 26/07 : server_altis.cfg puis calibrer_toucher).
cd /home/younes/arma3-marl/leviathan
pkill -f 'python3 calibrer' 2>/dev/null
sleep 3
nohup python3 calibrer_toucher.py --theatre altis --zone 23000,17400 \
  --duree 60 --reps 12 --out courbe_toucher.json > /tmp/courbe1.log 2>&1 &
echo "lance (pid $!)"
