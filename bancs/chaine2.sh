#!/bin/bash
cd /home/younes/arma3-marl
while pgrep -f "un_bras.sh|chaine.sh" > /dev/null; do sleep 30; done
echo "=== chaine precedente terminee, reprise du NATIF (FSM rendu) ==="
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
sleep 8
bash /mnt/c/Users/Public/un_bras.sh natif 20
echo "=== NATIF REPARE TERMINE ==="
