#!/bin/bash
LEV=/home/younes/arma3-marl/leviathan
pkill -f mesurer_repartition 2>/dev/null; pkill -f mesurer_suppression 2>/dev/null; sleep 2
bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
cd $LEV
python3 attendre_pont.py altis || { echo 'pont jamais pret'; echo REPART_FIN; exit 1; }
sleep 8
python3 mesurer_repartition2.py --theatre altis 2>&1
echo REPART_FIN
