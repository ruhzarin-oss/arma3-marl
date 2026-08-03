#!/usr/bin/env bash
# eval_v6.sh <poids> [graine] — evaluation d un reseau v6 : MEME PIPELINE QU A L ENTRAINEMENT.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
PY=/home/younes/env_isaaclab/bin/python3
P="$1"; G="${2:-1000}"; N=$(basename "$P" .pt)
for b in 0.9 1.6 2.2 3.5; do
  $PY banc_mission.py --pilote "reseau:$P" --episodes 1024 --graine "$G" --pas 80 \
      --budget "$b" --reflexe --journal "journaux/evb_${N}_b${b}_g${G}.jsonl" >/dev/null 2>&1
done
$PY lire_evb.py "$N" "$G"
