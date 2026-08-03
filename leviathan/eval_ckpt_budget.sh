#!/usr/bin/env bash
# eval_ckpt_budget.sh <poids> [graine] — evaluation DANS LE MONDE A BUDGET.
# eval_checkpoint.sh evalue dans le monde a VERBE : un agent v5 y voit des entrees qu il n a
# jamais rencontrees, et on lit 4,3 % au lieu du vrai taux. Meme faute que la sonde : changer
# le monde pour l entrainement et pas pour la mesure.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
PY=/home/younes/env_isaaclab/bin/python3
P="$1"; G="${2:-1000}"; N=$(basename "$P" .pt)
for b in 0.9 1.6 2.2 3.5; do
  $PY banc_mission.py --pilote "reseau:$P" --episodes 1024 --graine "$G" --pas 80 \
      --budget "$b" --journal "journaux/evb_${N}_b${b}_g${G}.jsonl" >/dev/null 2>&1
done
$PY lire_evb.py "$N" "$G"
