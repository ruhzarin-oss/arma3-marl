#!/bin/bash
# TEST DE FUMEE AVANT NEUF HEURES ⟨regle : verifier avant run couteux⟩.
# Un episode par decodeur. On verifie que l echantillonnage se produit REELLEMENT cote pont
# (les actions varient), que la graine se journalise, et que le releve npz sort.
cd /home/younes/arma3-marl || exit 1
mkdir -p /mnt/data/fumee
for D in echantillon argmax; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
  sleep 3; rm -f /tmp/releve_live.npz
  HMT_SESSION="_fum$D" HMT_DECODEUR=$D HMT_GRAINE_ACT=7 HMT_TAU=1.0 \
    timeout 640 ./.venv/bin/python banc_live.py politique > /mnt/data/fumee/$D.txt 2>&1
  [ -f /tmp/releve_live.npz ] && cp /tmp/releve_live.npz /mnt/data/fumee/$D.npz
  echo "$D fini $(date +%H:%M)" >> /mnt/data/fumee/journal.txt
done
echo TERMINE >> /mnt/data/fumee/journal.txt
