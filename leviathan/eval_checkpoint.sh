#!/usr/bin/env bash
# eval_checkpoint.sh <poids> — LA SEULE COURBE QUI COMPTE.
# Invoque l instrument certifie au jalon 1 sur un point de controle. Ce n est pas une sonde
# neuve : c est le banc qui a prouve son zero sur les six doctrines.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
PY=/home/younes/env_isaaclab/bin/python3
P="$1"; G="${2:-1000}"
for v in prendre infiltrer; do
  $PY banc_mission.py --pilote "reseau:$P" --verbe $v --episodes 1024 --graine $G       --pas 80 --mode episode --journal "journaux/ckpt_$(basename $P .pt)_${v}_g${G}.jsonl"       >/dev/null 2>&1
done
$PY analyse_journal.py "journaux/ckpt_$(basename $P .pt)_*_g${G}.jsonl" 2>&1 | grep -E "prendre|infiltrer|REFUSEE"
