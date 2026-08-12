#!/bin/bash
# lancer_boucle.sh — lance l entrainement DETACHE.
# Le motif du script ne figure pas dans la commande ssh, donc aucun pkill ne peut se
# retourner contre l appelant. Troisieme fois que ce piege se referme : relancer.sh le
# documente deja pour les serveurs Arma, il valait pour python aussi.
cd /home/younes/arma3-marl
for P in $(pgrep -f "[b]oucle\.py"); do kill "$P" 2>/dev/null; done
sleep 2
setsid nohup ./.venv/bin/python boucle.py "${1:-400}" > /tmp/boucle_run.txt 2>&1 < /dev/null &
sleep 3
echo "PID : $(pgrep -f '[b]oucle\.py' | head -1)"
