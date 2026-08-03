#!/bin/bash
# Redemarre MELTEMI proprement. Passer par ce script et pas par une commande ssh directe.
pkill -f 'arma3server_x64' 2>/dev/null
sleep 6
nohup bash /mnt/data/harmattan-sandbox/launch_altis.sh > /tmp/meltemi_boot.log 2>&1 &
echo relance
