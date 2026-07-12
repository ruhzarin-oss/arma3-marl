#!/bin/bash
cd /home/younes/arma3-marl/leviathan && source ~/arma3-marl/.venv/bin/activate 2>/dev/null
LOG=/home/younes/repertoire_chain.log
run(){ echo ">>> BRIQUE $2 — $(date +%H:%M)" >> "$LOG"; CUDA_VISIBLE_DEVICES=0 python brick_train.py --env "$1" --tag "$2" --metric "$3" --nact "$4" --iters 600 --envs 4096 >> "$LOG" 2>&1; }
run at_env:AtEnv             at        destroyed 9
run marksman_env:MarksmanEnv marksman  hvt_down  5
run medic_env:MedicEnv       medic     revived   8
run mg_env:MgEnv             mg        held      9
echo "=== BATCH2 TERMINÉ $(date +%H:%M) ===" >> "$LOG"
