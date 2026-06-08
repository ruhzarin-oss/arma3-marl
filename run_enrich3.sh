#!/bin/bash
set -u; PY=/mnt/steam/harmattan/venvs/rl/bin/python; cd /home/younes/arma3-marl
echo "[enrich3] $(date +%H:%M:%S) ligue MANŒUVRE + timeout décisif (--no_attrition --timeout_decisive)..."
$PY train_league_gpu.py --iters 300 --envs 98304 --no_attrition --timeout_decisive --save league_maneuver3
echo "[enrich3] $(date +%H:%M:%S) fini -> diagnostic :"
$PY enrich_check3.py 2>&1 | grep -vE "warn|CUDA capab|pytorch.org|queued_call|^- |^The |^Please|^  _|sm_61|sm_75"
echo "[enrich3] $(date +%H:%M:%S) FINI"
