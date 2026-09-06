#!/bin/bash
# suite_b0_g1 — L'ORDRE EST CONTRAIGNANT (voir PROTOCOLE_MATIN.md) :
# temoins d'abord, porte ensuite, et la porte ne se joue PAS si un temoin sort de sa bande.
cd /home/younes/arma3-marl
exec > suite_g1.log 2>&1
echo "en attente de la fin de la graine 1... $(date +%H:%M:%S)"
while pgrep -f "harnais.py .* --graine 1 " > /dev/null; do sleep 20; done
sleep 20
echo "graine 1 terminee a $(date +%H:%M:%S)"
tail -2 graine1.log

echo ""
echo "################ 1. LES TEMOINS ################"
echo "bandes exigees : DOCTRINE dans [93,0 ; 100]   ALEATOIRE dans [5,5 ; 23,4]"
./.venv/bin/python -u temoins_traversants.py --n 51
echo "(code de sortie des temoins : $?)"

echo ""
echo "################ 2. LA PORTE ################"
P=$(ls -t ckpt_b0_g1/*.pt | head -1)
echo "point juge : $P"
./.venv/bin/python -u porte_b0.py --point "$P"
echo "(code de sortie de la porte : $?)"
echo "fini $(date +%H:%M:%S)"
