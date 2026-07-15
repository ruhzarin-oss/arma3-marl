#!/bin/bash
cd /home/younes/arma3-marl/leviathan
pkill -9 -f coevo_rl2
sleep 2
rm -f coevo_rl2.log
/home/younes/arma3-marl/.venv/bin/python coevo_rl2.py > coevo_rl2.log 2>&1
