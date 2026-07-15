#!/bin/bash
cd /home/younes/isaaclab_src
export OMNI_KIT_ACCEPT_EULA=YES
pkill -9 -f play_dlssoff
sleep 3
CKPT=/home/younes/isaaclab_src/logs/skrl/g1_flat/2026-07-09_09-21-28_ppo_torch/checkpoints/best_agent.pt
rm -f /home/younes/arma3-marl/g1walk.log
/home/younes/env_isaaclab/bin/python scripts/reinforcement_learning/skrl/play_dlssoff.py \
  --task Isaac-Velocity-Flat-G1-Play-v0 --checkpoint "$CKPT" --num_envs 1 --video --video_length 180 --headless \
  > /home/younes/arma3-marl/g1walk.log 2>&1
