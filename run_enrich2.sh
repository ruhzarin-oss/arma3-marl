#!/bin/bash
set -u
PY=/mnt/steam/harmattan/venvs/rl/bin/python
cd /home/younes/arma3-marl
echo "[enrich2] $(date +%H:%M:%S) ligue MANŒUVRE + capture atteignable (--no_attrition --secure_n 1 --cap_need 3)..."
$PY train_league_gpu.py --iters 300 --envs 98304 --no_attrition --secure_n 1 --cap_need 3 --save league_maneuver2
echo "[enrich2] $(date +%H:%M:%S) entraînement fini -> diagnostic :"
$PY enrich_check2.py 2>&1 | grep -vE "warn|CUDA capab|pytorch.org|queued_call|^- |^The |^Please|^  _|sm_61|sm_75"
echo "[enrich2] $(date +%H:%M:%S) FINI"
