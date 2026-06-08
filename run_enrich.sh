#!/bin/bash
# Enrichissement : entraîne une ligue en MODE MANŒUVRE (capture, pas attrition) puis diagnostique
# si l'exécuteur sait enfin AVANCER/CAPTURER (vs l'ancien league_learner). Détaché + log persistant.
set -u
PY=/mnt/steam/harmattan/venvs/rl/bin/python
cd /home/younes/arma3-marl
echo "[enrich] $(date +%H:%M:%S) entraînement ligue MODE MANŒUVRE (300 it, --no_attrition)..."
$PY train_league_gpu.py --iters 300 --envs 98304 --no_attrition --save league_maneuver
echo "[enrich] $(date +%H:%M:%S) entraînement fini -> league_maneuver_learner.pt"
echo "[enrich] $(date +%H:%M:%S) diagnostic AVANCER/capture :"
$PY enrich_check.py 2>&1 | grep -vE "warn|CUDA capab|pytorch.org|queued_call|^- |^The |^Please|^  _|sm_61|sm_75"
echo "[enrich] $(date +%H:%M:%S) FINI"
