#!/bin/bash
# PORTE B0@60 EN TRANSFERT ZERO-SHOT.
# ⚠️ L'objet juge est le point CERTIFIE B0@30, intact, jamais entraine a 60 m.
# C'est ce qui rend la revendication « zero-shot » vraie au sens litteral.
# Les deux graines, une par instance, en parallele.
cd /home/younes/arma3-marl
exec > porte60.log 2>&1
echo "debut $(date +%H:%M:%S)"
echo "porte 93,0 % = borne basse de Wilson de la doctrine MESUREE CE SOIR a 60 m (51/51)."
echo "Elle vaut le meme nombre qu'a 30 m par coincidence d'un 51/51 a n=51, jamais par recopie."
echo ""
./.venv/bin/python -u porte_b0.py --point ckpt_b0/pt_001992.pt    --D 60 --instance 1 > p60_g0.log 2>&1 &
A=$!
./.venv/bin/python -u porte_b0.py --point ckpt_b0_g1/pt_001992.pt --D 60 --instance 2 > p60_g1.log 2>&1 &
B=$!
echo "graine 0 -> instance 1 (pid $A)   graine 1 -> instance 2 (pid $B)"
wait $A; wait $B
echo ""; echo "############ GRAINE 0 ############"; cat p60_g0.log
echo "############ GRAINE 1 ############"; cat p60_g1.log
echo "fini $(date +%H:%M:%S)"
