#!/bin/bash
# Serveur neuf, pont prouve libre, PUIS le banc. Un run tue laisse le pont occupe :
# c'est ce qui a fait echouer le controle de terrain a 10:34.
LEV=/home/younes/arma3-marl/leviathan
pkill -f mesurer_suppression 2>/dev/null; sleep 2
bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
cd $LEV
python3 attendre_pont.py altis || { echo 'pont jamais pret'; echo VRAIBANC_TERMINE; exit 1; }
sleep 8
python3 mesurer_suppression.py --theatre altis --reps 3 --duree 60 2>&1
echo VRAIBANC_TERMINE
