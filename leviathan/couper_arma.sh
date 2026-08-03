#!/bin/bash
# Coupe le serveur Arma. Passer par ce script : un pkill dont le motif figure dans sa
# propre ligne de commande ssh se tue lui-meme (arrive 3x le 26/07).
pkill -f 'arma3server_x64' 2>/dev/null
sleep 5
pkill -9 -f 'arma3server_x64' 2>/dev/null
sleep 2
pgrep -f 'arma3server_x64' >/dev/null && echo 'encore vivant' || echo 'serveur Arma coupe'
