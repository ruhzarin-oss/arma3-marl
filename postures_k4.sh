#!/bin/bash
# LES POSTURES, POUR DE VRAI — 1 200 iterations, k = 4 graines, DEUX bras.
# Pre-inscription : PREINSCRIPTION_POSTURES.md (b3626e1), AMENDEE ce jour (voir le .md).
# ⚠️ La premiere tentative (23/08) tournait a 140 iterations et rendait 0 % : elle mesurait
# le BUG DE BUDGET, pas les postures. L experience n a donc jamais eu lieu.
# ⚠️ k identique dans les deux bras, fixe d avance ⟨Fable⟩. Et la porte juge sur SELECT :
# on ne brule pas TEST pour de l exploratoire.
cd /home/younes/arma3-marl || exit 1
export HMT_PORTE=select
for NA in 10 13; do
  for G in 0 1 2 3; do
    OUT=/home/younes/arma3-marl/pol_k4_na${NA}_g${G}
    # deja fait ? (les graines 0 et 1 a 10 actions existent depuis le 23/08, mais elles ont
    # ete jugees sur TEST : on les rejoue pour que les huit runs soient comparables)
    if [ -f "${OUT}_PASSE.pt" ] || [ -f "${OUT}_TOMBE.pt" ]; then continue; fi
    L=/mnt/data/k4_na${NA}_g${G}.log; : > "$L"
    HMT_NA=$NA HMT_SEED=$G HMT_PT=${OUT}.pt \
      ./.venv/bin/python -u boucle.py 1200 >> "$L" 2>&1
    echo "na=$NA graine=$G fini $(date +%H:%M)" >> /mnt/data/k4_journal.txt
  done
done
echo TERMINE >> /mnt/data/k4_journal.txt
