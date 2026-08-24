#!/bin/bash
# LE FILM — graines 0 et 1, un point toutes les 50 iterations, meme recette.
# Question : l argmax de la graine perdante n a-t-il JAMAIS ete bon, ou s est-il DEFAIT ?
cd /home/younes/arma3-marl || exit 1
export HMT_NA=10 HMT_CKPT_EVERY=50
for G in 0 1; do
  D=/mnt/data/film_g${G}; mkdir -p "$D"; rm -f "$D"/*.pt
  export HMT_SEED=$G HMT_CKPT="$D"
  export HMT_PT=/home/younes/arma3-marl/pol_film_g${G}.pt
  L=/mnt/data/film_g${G}.log; : > "$L"
  { echo "═══ FILM graine $G — debut $(date +%H:%M:%S) ═══"
    ./.venv/bin/python -u boucle.py 1200
    echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
  echo "graine $G filmee $(date +%H:%M) — $(ls "$D"/*.pt | wc -l) points" >> /mnt/data/film_journal.txt
done
echo TERMINE >> /mnt/data/film_journal.txt
