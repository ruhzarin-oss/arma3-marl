#!/bin/bash
# A/B propre : attend la fin de la ligue BROUILLARD (league_fog), puis lance l'omniscient APPARIÉ.
# Mêmes réglages exactement (envs/iters/seed), seule différence = sight (1e9 = omniscient).
set -u
PY=/mnt/steam/harmattan/venvs/rl/bin/python
cd /home/younes/arma3-marl

echo "[ab] attente fin ligue brouillard (league_fog)..."
while pgrep -f "train_league_gpu.py.*--save league_fog" >/dev/null 2>&1; do sleep 30; done
echo "[ab] brouillard terminé -> lancement omniscient apparié (league_omni, sight=1e9)"
$PY train_league_gpu.py --iters 300 --envs 98304 --sight 1e9 --save league_omni
echo "[ab] omniscient terminé -- les deux bras A/B sont prêts (league_fog_learner.pt + league_omni_learner.pt)"
