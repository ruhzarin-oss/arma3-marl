#!/bin/bash
# CHAINE DE NUIT — l'ordre est contraignant (PRE_SITE_DEGELE.md) :
#   1. on attend la fin des deux courses (regle d'arret ou 4000 episodes)
#   2. TEMOINS, un par instance — un temoin ne garde que SON instance, lecon du 02/09
#   3. la porte, seulement si les deux temoins tiennent leur bande
cd /home/younes/arma3-marl
exec > chaine_nuit.log 2>&1
echo "veille armee a $(date +%H:%M:%S)"
while pgrep -f "harnais.py .* --sites apprentissage" > /dev/null; do sleep 60; done
echo "les deux courses ont fini a $(date +%H:%M:%S)"
grep -E "ARRET A ISSUE|^FIN :" site_g0.log site_g1.log
sleep 30

echo ""
echo "############ 1. TEMOINS, UN PAR INSTANCE ############"
echo "bandes exigees : DOCTRINE >= 97,6 %   ALEATOIRE dans [5,5 ; 23,4]"
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 51 \
    --temoins DOCTRINE  --sites jugement --dimensionner > t_i1.log 2>&1 &
X=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 \
    --temoins DOCTRINE  --sites jugement --dimensionner > t_i2.log 2>&1 &
Y=$!
wait $X; wait $Y
D1=$(grep -o "DOCTRINE : [0-9]*/[0-9]* = [0-9.]*" t_i1.log | grep -o "[0-9.]*$")
D2=$(grep -o "DOCTRINE : [0-9]*/[0-9]* = [0-9.]*" t_i2.log | grep -o "[0-9.]*$")
echo "instance 1 : $(grep 'DOCTRINE :' t_i1.log)"
echo "instance 2 : $(grep 'DOCTRINE :' t_i2.log)"
OK=$(echo "$D1 $D2" | awk '{print ($1 >= 97.6 && $2 >= 97.6) ? 1 : 0}')
if [ "$OK" != "1" ]; then
  echo ""
  echo "############ ARRET : UN TEMOIN EST HORS DE SA BANDE ############"
  echo "La porte NE SE JOUE PAS. Le monde a bouge pendant la nuit ; juger l'agent"
  echo "contre une cible mesuree hier serait la faute que le registre du 16/08 a coutee."
  echo "fini $(date +%H:%M:%S)"
  exit 1
fi

echo ""
echo "############ 2. LA PORTE, sur les 126 sites de JUGEMENT ############"
P0=$(ls -t ckpt_site_g0/*.pt | head -1)
P1=$(ls -t ckpt_site_g1/*.pt | head -1)
echo "points juges : $P0  et  $P1"
echo "rappel du niveau AVANT entrainement sur sites tires, meme lot de jugement :"
echo "   graine 0 : 90,9 %  (1/5 series)      graine 1 : 82,0 %  (1/5 series)"
echo ""
./.venv/bin/python -u porte_b0.py --point "$P0" --D 30 --instance 1 \
    --sites jugement --transfert > p_site_g0.log 2>&1 &
A=$!
./.venv/bin/python -u porte_b0.py --point "$P1" --D 30 --instance 2 \
    --sites jugement --transfert > p_site_g1.log 2>&1 &
B=$!
wait $A; wait $B
echo "############ GRAINE 0 ############"; cat p_site_g0.log
echo "############ GRAINE 1 ############"; cat p_site_g1.log
echo "fini $(date +%H:%M:%S)"
