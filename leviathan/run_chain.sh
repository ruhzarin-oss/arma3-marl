#!/bin/bash
# run_chain.sh — entraîne une LISTE de briques en séquence (autonome). Une brique = env:Class tag metric nact.
cd /home/younes/arma3-marl/leviathan && source ~/arma3-marl/.venv/bin/activate 2>/dev/null
LOG=/home/younes/repertoire_chain.log
run(){ echo ">>> BRIQUE $2 — $(date +%H:%M)" >> "$LOG"; CUDA_VISIBLE_DEVICES=0 python brick_train.py --env "$1" --tag "$2" --metric "$3" --nact "$4" --iters 600 --envs 4096 >> "$LOG" 2>&1; }
# --- briques validées (smoke OK) ---
run soutien_env:SoutienEnv   soutien   ally_survived 8
run grenade_env:GrenadeEnv   grenade   cleared       3
echo "=== BATCH TERMINÉ $(date +%H:%M) ===" >> "$LOG"
