#!/bin/bash
cd /home/younes/arma3-marl
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "===== ABONDANCE (munitions quasi-illimitees -> escouade fainEante) =====" > ammo_ab.log
.venv/bin/python train_koth_gpu.py --iters 300 --ammo --ammo_max 100000 --save kothammo_abond >> ammo_ab.log 2>&1
echo "===== RARETE (40 munitions -> escouade ingenieuse) =====" >> ammo_ab.log
.venv/bin/python train_koth_gpu.py --iters 300 --ammo --ammo_max 40 --save kothammo_rare >> ammo_ab.log 2>&1
echo "===== TERMINE =====" >> ammo_ab.log
