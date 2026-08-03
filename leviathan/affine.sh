#!/usr/bin/env bash
# affine.sh — AFFINAGE PPO DEPUIS LE CLONE. Recette SHAMAL validee : imiter, puis affiner.
# Repere mesure AVANT de demarrer : clone a 30,0 % de succes a B=0,9 et 64,0 % a B=2,2,
# arrivee 76 %. Professeur a 96,2 % d arrivee.
# Petit pas (5e-5) pour ne pas effacer le clone. Tous les points de controle conserves.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
G="${G:-0}"
mkdir -p ckpt
for etape in 50 100 150 200; do
  iter0=$((etape-50))
  if [ $iter0 -eq 0 ]; then reprise="--reprise ckpt/clone.pt"; else reprise="--reprise ckpt/aff_g${G}_${iter0}.pt"; fi
  $PY train_mission.py --iters 50 --envs 4096 --D 8 --seed $G --budget --lagrangien \
      --Bmin 0.6 --Bmax 2.5 --lr 5e-5 --iters_total 200 --iter0 $iter0 \
      --out ckpt/aff_g${G}_${etape}.pt $reprise 2>&1 | grep -vE "Warning|warn" | grep -E "reprise|lambda" | tail -2
  for b in 0.9 2.2; do
    $PY banc_mission.py --pilote "reseau:ckpt/aff_g${G}_${etape}.pt" --episodes 2048 \
        --graine 1000 --pas 80 --budget $b \
        --journal "journaux/aff_g${G}_${etape}_b${b}.jsonl" >/dev/null 2>&1
  done
  $PY lire_lag.py "aff_g${G}_${etape}"
done
echo "AFFINE_DONE"
