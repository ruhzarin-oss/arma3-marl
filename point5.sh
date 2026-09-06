#!/bin/bash
# POINT 5 — SONDE DE VACANCE DU BARREAU B1i.
# ⟨Fable⟩ « Politique degelee, zero-shot sur B1 arme, 126 sites.
#   >= 95 % -> barreau VIDE, on ne lance rien
#   <= 85 % -> vivant, marge suffisante
#   entre les deux -> rapprocher le defenseur et refaire (3) »
# ⚠️ La politique degelee n'a AUCUN canal de menace : elle ne peut pas voir le cone.
# Si elle passe quand meme, c'est que le barreau ne demande pas de le voir.
cd /home/younes/arma3-marl
exec > point5.log 2>&1
echo "debut $(date +%H:%M:%S)"
echo "temoins du barreau B1i : DOCTRINE 62,7 %  ·  ALEATOIRE 0,0 %"
echo ""
P0=$(ls -t ckpt_site_g0/*.pt | head -1)
P1=$(ls -t ckpt_site_g1/*.pt | head -1)
echo "points juges : $P0  et  $P1"
./.venv/bin/python -u porte_b0.py --point "$P0" --D 30 --instance 1 --barreau B1i \
    --sites jugement --transfert > p5_g0.log 2>&1 &
A=$!
./.venv/bin/python -u porte_b0.py --point "$P1" --D 30 --instance 2 --barreau B1i \
    --sites jugement --transfert > p5_g1.log 2>&1 &
B=$!
wait $A; wait $B
echo ""
echo "############ GRAINE 0 ############"; grep -E "serie|series au-dessus|VERDICT" p5_g0.log
echo "############ GRAINE 1 ############"; grep -E "serie|series au-dessus|VERDICT" p5_g1.log
echo ""
echo "=== TEMOIN PAR INSTANCE, joue APRES (un temoin ne garde que son instance) ==="
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 51 --barreau B1i --capdef \
    --temoins DOCTRINE --sites jugement --dimensionner > p5_t1.log 2>&1 &
X=$!
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 --barreau B1i --capdef \
    --temoins DOCTRINE --sites jugement --dimensionner > p5_t2.log 2>&1 &
Y=$!
wait $X; wait $Y
echo "  instance 1 : $(grep 'DOCTRINE :' p5_t1.log)"
echo "  instance 2 : $(grep 'DOCTRINE :' p5_t2.log)"
echo "fini $(date +%H:%M:%S)"
