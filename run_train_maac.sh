#!/usr/bin/env bash
# Lance l'entrainement MAAC, detache. Tue aussi le durci concatene (verdict acquis) pour liberer le GPU.
pkill -9 -f "python train_commander_maac.py" 2>/dev/null
pkill -9 -f "python train_commander.py" 2>/dev/null
sleep 3
cd /home/younes/arma3-marl || exit 1
: > /home/younes/compose-embodiment/commander_maac_train.log
source .venv/bin/activate
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=1
exec python train_commander_maac.py >> /home/younes/compose-embodiment/commander_maac_train.log 2>&1
