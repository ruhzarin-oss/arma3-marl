#!/bin/bash
LEV=/home/younes/arma3-marl/leviathan
bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
cd $LEV
python3 attendre_pont.py altis || { echo VRAIBANC_TERMINE; exit 1; }
sleep 10
python3 mesurer_suppression.py --reps 3 --duree 60 2>&1
echo VRAIBANC_TERMINE
