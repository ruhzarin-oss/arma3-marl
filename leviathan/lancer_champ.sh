#!/bin/bash
cd /home/younes/arma3-marl
./.venv/bin/python leviathan/voir_champ.py --graines 3 --rounds 150 --K 8 --ne 1024 --eval 300   --out voir_champ.json > /tmp/champ.log 2>&1
echo CHAMP_TERMINE >> /tmp/champ.log
