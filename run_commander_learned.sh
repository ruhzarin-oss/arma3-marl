#!/usr/bin/env bash
# Lance le deploiement live du commandant APPRIS, detache (survit au drop ssh).
pkill -9 -f "python b1_commander_learned.py" 2>/dev/null
sleep 2
rm -f "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis/hmt_bridge/"cmd_*.sqf 2>/dev/null
cd /home/younes/arma3-marl || exit 1
: > commander_learned.log
source .venv/bin/activate
exec python b1_commander_learned.py >> commander_learned.log 2>&1
