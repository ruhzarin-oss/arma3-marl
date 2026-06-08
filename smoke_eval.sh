#!/bin/bash
# Smoke fonctionnel du harnais d'éval : 2 serveurs, brain=ref=prod, éval courte. Prouve le bout-en-bout.
set -u
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
cd /home/younes/arma3-marl

echo "[smoke] boot 2 serveurs..."
bash "$SB/multi_server.sh" 2 >/dev/null 2>&1
for w in $(seq 1 36); do
  ready=0
  for i in 0 1; do grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1)); done
  [ "$ready" -ge 2 ] && { echo "[smoke] 2/2 missions chargées (${w}x5s)"; break; }
  sleep 5
done
sleep 10

echo "[smoke] éval 20 pas..."
$PY eval_koth_arma.py --brain league_learner.pt --ref league_learner.pt --servers 2 --per_server 2 --steps 20 --out /tmp/smoke_eval.json --label SMOKE

echo "[smoke] JSON résultat :"; cat /tmp/smoke_eval.json 2>/dev/null
echo "[smoke] coupe les 2 serveurs..."; pkill -9 -f arma3server_x64
echo "[smoke] FINI"
