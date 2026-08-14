#!/bin/bash
cd /home/younes/arma3-marl
L=/mnt/data/harmattan-sandbox/logs/live20
mkdir -p $L; rm -f $L/*
echo "=== 20 EPISODES — banc live 4 contre 4, site (4644,5652) ==="
for i in $(seq 1 20); do
  rm -f /tmp/releve_live.npz
  bash lancer_live.sh > /dev/null 2>&1
  ok=0
  for w in $(seq 1 200); do
    [ -f /tmp/releve_live.npz ] && { ok=1; break; }
    sleep 5
  done
  if [ "$ok" = 1 ]; then
    cp /tmp/releve_live.npz $L/ep_$i.npz
    cp /tmp/banc_live.txt   $L/ep_$i.txt
    S=$(grep -o 'HARMATTAN_SCENE def=[0-9]* att=[0-9]*' $L/ep_$i.txt | tail -1)
    F=$(grep -o 'fin au pas [0-9]*' $L/ep_$i.txt | tail -1)
    echo "  episode $i  OK   $S   ${F:-60 pas}"
  else
    cp /tmp/banc_live.txt $L/ep_${i}_ECHEC.txt 2>/dev/null
    echo "  episode $i  ECHEC (pas de releve apres 16 min)"
  fi
done
# on rend la machine
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
pkill -f '[b]anc_live\.py' 2>/dev/null
echo "=== TERMINE : $(ls $L/ep_*.npz 2>/dev/null | wc -l) releves sur 20 ==="
