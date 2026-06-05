#!/bin/bash
cd /home/younes/arma3-marl
for i in 1 2 3 4 5 6; do pkill -9 -f live_arena_sp; sleep 1; done
B="/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser"
rm -f "$B/Documents/Arma 3/missions/HarmattanKoth.Altis/hmt_bridge/"cmd_*.sqf
sleep 1
nohup .venv/bin/python -u live_arena_sp.py > logs_train/arena_sp.log 2>&1 &
disown
sleep 1
echo "lance, arenes actives=$(pgrep -f live_arena_sp | wc -l)" > /home/younes/arma3-marl/logs_train/launch_status.txt
