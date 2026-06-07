#!/bin/bash
# REPRISE table v3 : boot 16 serveurs -> resume_v3.py (M6 seeds 1,8 + M7 0..15, append).
# Détaché de la session + log persistant. NE touche PAS au jsonl existant (resume_v3.py append-only).
set -u
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
N=16
cd /home/younes/arma3-marl

echo "[boot] lancement de $N serveurs..."
bash "$SB/multi_server.sh" $N
echo "[boot] attente du chargement des missions (max 240s)..."
for w in $(seq 1 48); do
  ready=0
  for i in $(seq 0 $((N-1))); do
    grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1))
  done
  echo "[boot] $ready/$N missions chargées (${w}x5s)"
  [ "$ready" -ge "$N" ] && break
  sleep 5
done
sleep 15

echo "############ REPRISE V3 (M6 1,8 + M7) ############"
$PY resume_v3.py --servers $N --max_steps 500
echo "############ FIN REPRISE V3 ############"
