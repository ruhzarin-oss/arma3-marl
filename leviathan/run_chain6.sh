#!/bin/bash
cd /home/younes/arma3-marl/leviathan && source ~/arma3-marl/.venv/bin/activate 2>/dev/null
LOG=/home/younes/repertoire_chain.log
run(){ echo ">>> BRIQUE $2 — $(date +%H:%M)" >> "$LOG"; CUDA_VISIBLE_DEVICES=0 python brick_train.py --env "$1" --tag "$2" --metric "$3" --nact "$4" --iters 600 --envs 4096 >> "$LOG" 2>&1; }
run grenadier_env:GrenadierEnv grenadier cleared 3
run mines_env:MinesEnv         mines     caught  9
run recup_env:RecupEnv         recup     saved   8
run ratissage_env:RatissageEnv ratissage found   8
echo "=== BATCH6 TERMINÉ $(date +%H:%M) ===" >> "$LOG"
