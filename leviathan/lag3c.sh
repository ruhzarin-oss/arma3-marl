#!/usr/bin/env bash
# lag3b.sh — ETAPE 3b : LE LAGRANGIEN. Criteres CRITERES_3B_LAGRANGIEN.md 392bbcd9c236d0f7
# Un seul changement par rapport au temoin : la contrainte devient un multiplicateur qui PART
# DE ZERO et ne se resserre que si l agent viole trop souvent. D abord la route, l economie ensuite.
# Portes rebasees sur la mesure : arrivee >= 25,3 % (temoin 28,3), violation <= 15 %, rho >= 0,90.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
G="${G:-0}"
mkdir -p ckpt
for etape in 100 200 300 400; do
  reprise=""; iter0=$((etape-100))
  [ $iter0 -gt 0 ] && reprise="--reprise ckpt/lag3c_g${G}_${iter0}.pt"
  $PY train_mission.py --iters 100 --envs 4096 --D 8 --seed $G --budget --lagrangien \
      --Bmin 0.6 --Bmax 4.2 --iters_total 400 --iter0 $iter0 \
      --out ckpt/lag3c_g${G}_${etape}.pt $reprise 2>&1 | grep -vE "Warning|warn" | grep -E "lambda|it +[0-9]+ \|" | tail -2
  for b in 0.9 2.2; do
    $PY banc_mission.py --pilote "reseau:ckpt/lag3c_g${G}_${etape}.pt" --episodes 2048 \
        --graine 1000 --pas 80 --budget $b \
        --journal "journaux/lag3c_g${G}_${etape}_b${b}.jsonl" >/dev/null 2>&1
  done
  $PY lire_lag.py "lag3c_g${G}_${etape}"
done
echo "LAG3B_DONE"
