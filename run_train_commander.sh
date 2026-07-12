#!/usr/bin/env bash
# Lance l'entrainement du commandant appris, detache (survit au drop ssh). Tue l'ancien, log frais.
pkill -9 -f "python train_commander.py" 2>/dev/null   # cible le PYTHON, pas ce script (dont le chemin contient train_commander)
sleep 2
cd /home/younes/arma3-marl || exit 1
: > /home/younes/compose-embodiment/commander_train.log
source .venv/bin/activate
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=1
exec python train_commander.py >> /home/younes/compose-embodiment/commander_train.log 2>&1
