#!/bin/bash
cd /home/younes/arma3-marl
export OMNI_KIT_ACCEPT_EULA=YES
pkill -9 -f isaac_build_world
sleep 3
rm -f isaac_athens.png isaac_build5.log
/home/younes/env_isaaclab/bin/python isaac_build_world.py --headless --enable_cameras > isaac_build5.log 2>&1
