#!/bin/bash
cd /home/younes/arma3-marl
export OMNI_KIT_ACCEPT_EULA=YES
pkill -9 -f isaac_g1_athens
sleep 3
rm -f isaac_g1_athens.png isaac_g1.log
/home/younes/env_isaaclab/bin/python isaac_g1_athens.py --headless --enable_cameras > isaac_g1.log 2>&1
