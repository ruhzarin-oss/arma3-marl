#!/bin/bash
cd /home/younes/arma3-marl
export OMNI_KIT_ACCEPT_EULA=YES
pkill -9 -f isaac_g1_hulldown
sleep 3
rm -f g1_debout.png g1_accroupi.png isaac_hd.log
/home/younes/env_isaaclab/bin/python isaac_g1_hulldown.py --headless --enable_cameras > isaac_hd.log 2>&1
