#!/bin/bash
cd /home/younes/arma3-marl/leviathan && source ~/arma3-marl/.venv/bin/activate 2>/dev/null
LOG=/home/younes/repertoire_chain.log
run(){ echo ">>> BRIQUE $2 — $(date +%H:%M)" >> "$LOG"; CUDA_VISIBLE_DEVICES=0 python brick_train.py --env "$1" --tag "$2" --metric "$3" --nact "$4" --iters 600 --envs 4096 >> "$LOG" 2>&1; }
run mission_env:MissionEnv orchestration cleared 5
run smoke_env:SmokeEnv     fumigene      reached 2
echo "=== BATCH4 TERMINÉ $(date +%H:%M) ===" >> "$LOG"
