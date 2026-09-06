#!/bin/bash
# SONDE DE VACANCE — voir PRE_SITE_DEGELE.md, ecrite AVANT.
# La politique CERTIFIEE a B0@30, gelee, sur 126 sites de jugement jamais vus.
# ⚠️ Transfert assume : le monde a change pour que le site voyage dans le ticket.
cd /home/younes/arma3-marl
exec > sonde_vacance.log 2>&1
echo "debut $(date +%H:%M:%S)"
echo "porte 93,0 % = doctrine ponctuelle (100,0 %) moins la marge de 7 points."
echo ""
./.venv/bin/python -u porte_b0.py --point ckpt_b0/pt_001992.pt    --D 30 --instance 1 \
    --sites jugement --transfert > sv_g0.log 2>&1 &
A=$!
./.venv/bin/python -u porte_b0.py --point ckpt_b0_g1/pt_001992.pt --D 30 --instance 2 \
    --sites jugement --transfert > sv_g1.log 2>&1 &
B=$!
echo "graine 0 -> instance 1 (pid $A)   graine 1 -> instance 2 (pid $B)"
wait $A; wait $B
echo ""; echo "############ GRAINE 0 ############"; cat sv_g0.log
echo "############ GRAINE 1 ############"; cat sv_g1.log
echo "fini $(date +%H:%M:%S)"
