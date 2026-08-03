#!/bin/bash
cd /home/younes/arma3-marl
./.venv/bin/python leviathan/voir_stress.py --graines 3 --rounds 150 --K 8 --ne 1024 --eval 300   --out voir_stress.json > /tmp/stress.log 2>&1
echo STRESS_TERMINE >> /tmp/stress.log
