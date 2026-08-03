#!/usr/bin/env bash
# v5.sh — L ORDRE DEVIENT UN BUDGET. Criteres CRITERES_V5_BUDGET.md 9274c81a3842a5e5.
# Changement unique par rapport a v4 : le monde a budget. Plage [0,6 - 4,2] fixee par la
# mesure de frontiere, pas par intuition : a 0,6 une solution connue reussit encore 30 %.
# Runner corrige : tous les points de controle conserves, pas d apprentissage decroissant,
# sonde de divergence-verbe a chaque evaluation.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
mkdir -p ckpt
TOTAL=400
for etape in 50 100 150 200 250 300 350 400; do
  reprise=""; iter0=$((etape-50))
  [ $iter0 -gt 0 ] && reprise="--reprise ckpt/v5_${iter0}.pt"
  $PY train_mission.py --iters 50 --envs 4096 --D 8 --seed 0 --budget --Bmin 0.6 --Bmax 4.2       --iters_total $TOTAL --iter0 $iter0 --out ckpt/v5_${etape}.pt $reprise       2>&1 | grep -vE "Warning|warn" | tail -1
  echo "--- BANC CERTIFIE, iteration $etape ---"
  bash eval_checkpoint.sh ckpt/v5_${etape}.pt 1000
  $PY sonde_verbe.py --budget --poids ckpt/v5_${etape}.pt 2>&1 | grep -E "divergence des ACTIONS|ecart de VALEUR"
done
echo "V5_DONE"
