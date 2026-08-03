#!/bin/bash
LEV=/home/younes/arma3-marl/leviathan
cd $LEV
bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
python3 attendre_pont.py altis || { echo SONDE_FIN; exit 1; }
sleep 10
timeout 300 python3 mesurer_repartition.py --theatre altis --fenetres 1 2>&1 | head -20
sleep 3
timeout 120 python3 sonde_riposte.py 2>&1
echo SONDE_FIN
