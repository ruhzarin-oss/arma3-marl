#!/bin/bash
# LE BUDGET SUFFIT-IL ? — 1 200 iterations, DEUX graines, rien d autre ne change.
#
# Ce qu on demontre : que le gymnase sait ENCORE fabriquer une politique. Aujourd hui il
# n en produit plus une seule qui batte une manoeuvre ecrite a la main, et sans ca il n y a
# plus de levier du tout — ni postures, ni cout d exposition, ni rien : chaque idee testee
# donnerait un agent rate, et on ne saurait jamais si c est l idee ou la recette.
#
# CE QUI EST DEJA MESURE (cfe6e86) :
#   140 iter -> 5,7 %   ·   420 iter -> 24,8 %, +12,0 contre la frontale (borne +8,7)
#   la courbe MONTAIT ENCORE a 419 : 0,8 % a 200, 6,2 % a 360, 10,5 % a 380, 16,4 % a 419
#   gamma innocente : 5,3 % contre 5,7 % a budget egal
#
# ⚠️ PREDICTION ECRITE AVANT DE LANCER :
#   P  a 1 200 iterations, la porte PASSE — G1 positif contre la frontale ET contre le flanc
#      (34,3 %), sur les DEUX graines.
#   Falsificateur : si la prise plafonne sous 34,3 % sur les deux graines, le budget n est
#   pas la reponse complete, et les trois defauts trouves dans le code (guidage divise par
#   les morts, pas de bootstrap a la troncature, avantage normalise pas par pas) deviennent
#   la piste — UN BRAS A LA FOIS.
#   ⚠️ Si les deux graines DIVERGENT (l une passe, l autre non), on ne cite ni l une ni
#   l autre : c est la recette qui est instable, et c est un resultat en soi.
#
# ⚠️ RIEN D AUTRE NE CHANGE : ni le monde, ni la recompense, ni les actions, ni le lecteur.
cd /home/younes/arma3-marl || exit 1
export HMT_NA=10
for G in 0 1; do
  L=/mnt/data/budget1200_g${G}.log; : > "$L"
  export HMT_SEED=$G
  export HMT_PT=/home/younes/arma3-marl/pol_1200_g${G}.pt
  { echo "═══ GRAINE $G — 1200 iterations — debut $(date +%H:%M:%S) ═══"
    ./.venv/bin/python -u boucle.py 1200
    echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
  echo "graine $G finie $(date +%H:%M)" >> /mnt/data/budget_journal.txt
done
echo TERMINE >> /mnt/data/budget_journal.txt
