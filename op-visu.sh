#!/bin/bash
# op-visu.sh — lance une op tracée DANS LA MISSION QUE TU JOUES (preview Eden, mode --editor).
# Usage :  bash op-visu.sh [M1..M7] [seed] [vitesse] [ennemi]
#   ennemi : normal 28 | pro 42 | hardcore 60 | nightmare 84   (defauts : M2, 1, 1, normal)
# Prérequis : Arma 3 client ouvert, mission HMT-EcoleDeGuerre chargée dans Eden, preview lancée (tu es en vue du dessus).
cd /home/younes/arma3-marl
exec /mnt/steam/harmattan/venvs/rl/bin/python run_op_visual.py --editor --maneuver "${1:-M2}" --seed "${2:-1}" --speed "${3:-1}" --enemy "${4:-normal}"
