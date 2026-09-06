#!/bin/bash
# POINT 3 — LE TEST D'EXISTENCE DU BARREAU.
# ⟨Fable⟩ « Armer le defenseur. C'est le test d'existence du barreau : doctrine sur les
# 126 sites doit tomber nettement sous 99,9 % — reussi si <= 85 % avec IC95 excluant 99,9.
# Sinon le barreau n'existe pas et on replace le defenseur avant toute autre chose. »
# Rappel du repere : la doctrine fait 1199/1200 = 99,9 % sur ces memes sites SANS defenseur.
cd /home/younes/arma3-marl
exec > point3.log 2>&1
echo "debut $(date +%H:%M:%S)"
for k in $(seq 1 30); do
  ok=0
  for i in 1 2; do
    R=$(ls -t /mnt/c/Users/Younes/hmtech$i/*.rpt 2>/dev/null | head -1)
    [ -n "$R" ] && grep -q "ETAT PRET" "$R" && ok=$((ok+1))
  done
  [ $ok -eq 2 ] && break
  sleep 10
done
echo "les deux instances repondent PRET"
echo ""
echo "=== NON-REGRESSION : le monde SANS defenseur est-il intact ? (exige >= 97,6 %) ==="
./.venv/bin/python -u temoins_traversants.py --instance 1 --D 30 --n 51 \
    --temoins DOCTRINE --sites jugement --dimensionner > p3_sansdef.log 2>&1 &
A=$!
echo "=== TEST D'EXISTENCE : le monde AVEC defenseur arme, cap tire ==="
./.venv/bin/python -u temoins_traversants.py --instance 2 --D 30 --n 51 --barreau B1 --capdef \
    --temoins DOCTRINE --sites jugement --dimensionner > p3_avecdef.log 2>&1 &
B=$!
wait $A; wait $B
echo ""
echo "  sans defenseur : $(grep 'DOCTRINE :' p3_sansdef.log)"
echo "  avec defenseur : $(grep 'DOCTRINE :' p3_avecdef.log)"
echo ""
R2=$(ls -t /mnt/c/Users/Younes/hmtech2/*.rpt | head -1)
echo "  caps de defenseur tires (10 premiers) :"
grep "DEFENSEUR" "$R2" | head -5 | sed 's/.*DEFENSEUR/    /'
echo "fini $(date +%H:%M:%S)"
