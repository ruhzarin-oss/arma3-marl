#!/bin/bash
cd /home/younes/arma3-marl/leviathan && source ~/arma3-marl/.venv/bin/activate 2>/dev/null
LOG=/home/younes/repertoire_chain.log
run(){ echo ">>> BRIQUE $2 — $(date +%H:%M)" >> "$LOG"; CUDA_VISIBLE_DEVICES=0 python brick_train.py --env "$1" --tag "$2" --metric "$3" --nact "$4" --iters 600 --envs 4096 >> "$LOG" 2>&1; }
run tail_envs:Repli2Env    repli2    score   2
run tail_envs:Marksman2Env marksman2 hvt     5
run tail_envs:CQBEnv       cqb       score   4
run tail_envs:MortierEnv   mortier   score   6
run tail_envs:DefenseEnv   defense   held    4
run tail_envs:ConduiteEnv  conduite  arrived 8
echo "=== BATCH7 (queue) TERMINÉ $(date +%H:%M) ===" >> "$LOG"
