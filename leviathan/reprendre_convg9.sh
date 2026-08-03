#!/bin/bash
# conv g9 est morte de memoire au lancement (il manquait 650 Mo sur 24 Go).
# Lecon : CINQ processus tiennent sur cette carte, pas six.
# On attend qu'une case libere sa place, puis on la relance dans le trou.
cd /home/younes/arma3-marl
while [ "$(pgrep -fc 'lire_carte.py --bras')" -ge 5 ]; do sleep 60; done
nohup ./.venv/bin/python leviathan/lire_carte.py   --bras conv --graine 9 --sans_repere --rounds 150 --K 8 --ne 1024 --eval 300   --out carte_conv_g9.json > /tmp/carte_conv_g9.log 2>&1 &
echo "conv g9 relancee a $(date +%H:%M)"
