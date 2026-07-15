#!/bin/bash
cd /home/younes/arma3-marl
export OMNI_KIT_ACCEPT_EULA=YES
pkill -9 -f make_athens_collision
sleep 3
rm -f athens_collision.usd mkcol.log
/home/younes/env_isaaclab/bin/python make_athens_collision.py --headless > mkcol.log 2>&1
