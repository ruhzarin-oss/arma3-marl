#!/bin/bash
# LIGNE 4 du critere : les quatre sabotages rejoues sur LE HASH que la porte certifie.
# traverse et tir sont passes au smoke ; il reste munitions (T4) et jambes (T5).
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/sabotages; mkdir -p $D
echo "socle : $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)  commit $(git rev-parse --short HEAD)" | tee $D/EMPREINTE.txt
for m in sabotage jambes; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
  echo "═══ sabotage « $m » — 3 tirages, on ATTEND des rouges $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
  HMT_SESSION="_S$m" timeout 500 ./.venv/bin/python -u prevol.py 3 $m 45 > $D/$m.txt 2>&1
  tail -6 $D/$m.txt | tee -a $D/JOURNAL.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ TERMINE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
