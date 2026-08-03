#!/usr/bin/env bash
# v6.sh — L ORDRE EST CABLE DANS LE CORPS. Criteres CRITERES_V6_REFLEXE.md 4420f233b5b301be.
# Les deux portes sont franchies AVANT tout entrainement : controle nul a zero exact sur les
# six politiques de reference, et obeissance sans apprentissage a rho de Spearman 1,000.
# L agent ne part donc plus apprendre a obeir : il part obeissant, il apprend a etre COMPETENT.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
mkdir -p ckpt
TOTAL=400
for etape in 50 100 150 200 250 300 350 400; do
  reprise=""; iter0=$((etape-50))
  [ $iter0 -gt 0 ] && reprise="--reprise ckpt/v6_${iter0}.pt"
  $PY train_mission.py --iters 50 --envs 4096 --D 8 --seed 0 --budget --reflexe \
      --Bmin 0.6 --Bmax 4.2 --iters_total $TOTAL --iter0 $iter0 \
      --out ckpt/v6_${etape}.pt $reprise 2>&1 | grep -vE "Warning|warn" | tail -1
  echo "--- BANC CERTIFIE, iteration $etape ---"
  bash eval_v6.sh ckpt/v6_${etape}.pt 1000
done
echo "V6_DONE"
