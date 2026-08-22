#!/bin/bash
# VERIFICATION AVANT 14 HEURES DE RUN : les deux bras partent-ils de la meme ligne ?
cd /home/younes/arma3-marl || exit 1
mkdir -p /mnt/data/verifdep
for BRAS in natif politique; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
  sleep 3
  HMT_SESSION="_vd$BRAS" timeout 640 ./.venv/bin/python banc_live.py $BRAS \
    > /mnt/data/verifdep/$BRAS.txt 2>&1
  echo "$BRAS fini $(date +%H:%M)" >> /mnt/data/verifdep/journal.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo TERMINE >> /mnt/data/verifdep/journal.txt
