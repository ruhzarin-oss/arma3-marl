#!/usr/bin/env bash
# Lance UN commandant proprement, detache (survit au drop ssh). Tue les anciens, nettoie, log frais.
SB=/mnt/data/harmattan-sandbox
pkill -9 -f "b1_commander" 2>/dev/null
sleep 2
rm -f "$SB/arma3server/mpmissions/HarmattanBridge14.Stratis/hmt_bridge/"cmd_*.sqf 2>/dev/null
cd /home/younes/arma3-marl || exit 1
: > cmd_live.log
source .venv/bin/activate
exec python b1_commander.py >> cmd_live.log 2>&1
