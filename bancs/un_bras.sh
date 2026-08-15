#!/bin/bash
cd /home/younes/arma3-marl
B=$1; N=$2
L=/mnt/data/harmattan-sandbox/logs/base_$B
mkdir -p $L; rm -f $L/*
echo "=== BASELINE $B — $N episodes ==="
for i in $(seq 1 $N); do
  rm -f /tmp/releve_live.npz
  for P in $(pgrep -f "[b]anc_live\.py"); do kill $P 2>/dev/null; done
  for P in $(pgrep -x arma3server_x64); do tr "\\0" " " < /proc/$P/cmdline | grep -q -- "-port=6062" && kill $P; done
  sleep 6
  setsid nohup ./.venv/bin/python banc_live.py $B > /tmp/banc_live.txt 2>&1 < /dev/null &
  ok=0; for w in $(seq 1 200); do [ -f /tmp/releve_live.npz ] && { ok=1; break; }; sleep 5; done
  if [ "$ok" = 1 ]; then
    cp /tmp/releve_live.npz $L/ep_$i.npz; cp /tmp/banc_live.txt $L/ep_$i.txt
    echo "  $B $i OK   $(grep -o "HARMATTAN_SCENE def=[0-9]* att=[0-9]*" $L/ep_$i.txt|tail -1)   $(grep -o "fin au pas [0-9]*" $L/ep_$i.txt|tail -1)"
  else echo "  $B $i ECHEC"; fi
done
echo "=== $B TERMINE : $(ls $L/ep_*.npz 2>/dev/null|wc -l)/$N ==="
