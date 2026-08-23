#!/bin/bash
# REJOUER LA GRAINE 1 — pour pouvoir enfin ouvrir la politique qui a echoue.
# 1 200 iterations, EXACTEMENT la meme recette qu a 23 h 15. Rien ne change sauf que
# l artefact est desormais CONSERVE, avec son verdict dans le nom.
cd /home/younes/arma3-marl || exit 1
export HMT_NA=10 HMT_SEED=1
export HMT_PT=/home/younes/arma3-marl/pol_1200_g1_rejeu.pt
L=/mnt/data/rejeu_g1.log; : > "$L"
{ echo "═══ GRAINE 1, REJEU — debut $(date +%H:%M:%S) ═══"
  ./.venv/bin/python -u boucle.py 1200
  echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
echo TERMINE >> /mnt/data/rejeu_journal.txt
