#!/bin/bash
cd /home/younes/arma3-marl
./.venv/bin/python leviathan/voir_arc.py --graines 3 --rounds 150 --K 8 --ne 1024 --eval 300   --out voir_arc.json > /tmp/arc.log 2>&1
echo "ARC_TERMINE" >> /tmp/arc.log
