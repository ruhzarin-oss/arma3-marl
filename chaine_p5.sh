#!/bin/bash
# Chaine : on attend la fin du reentrainement, puis le point 5 (sonde de vacance).
cd /home/younes/arma3-marl
exec > chaine_p5.log 2>&1
echo "veille armee a $(date +%H:%M:%S)"
while pgrep -f "harnais.py .* --sites apprentissage" > /dev/null; do sleep 60; done
sleep 20
echo "reentrainement fini a $(date +%H:%M:%S)"
grep -hE "ARRET A ISSUE|^FIN :" site_g0.log site_g1.log
echo "points refaits : $(ls ckpt_site_g0/*.pt 2>/dev/null | wc -l) et $(ls ckpt_site_g1/*.pt 2>/dev/null | wc -l)"
echo ""
/home/younes/arma3-marl/point5.sh
cat point5.log
