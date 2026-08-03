#!/bin/bash
cd /home/younes/arma3-marl
./.venv/bin/python leviathan/voir_champ2.py --graines 3 --rounds 150 --K 8 --ne 1024 --eval 300   --out voir_champ2.json > /tmp/champ2.log 2>&1
echo CHAMP2_TERMINE >> /tmp/champ2.log
