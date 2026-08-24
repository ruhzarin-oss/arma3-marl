#!/bin/bash
# REJEU INSTRUMENTE DE LA GRAINE 1 — meme recette, meme graine, aucun changement de
# comportement : l instrumentation journalise et n entre dans aucune perte.
# Question : quelle part de la norme du gradient revient aux pas OU UNE PRISE A LIEU,
# sous l avantage BRUT et sous l avantage NORMALISE PAS PAR PAS ?
cd /home/younes/arma3-marl || exit 1
export HMT_NA=10 HMT_SEED=1 HMT_INSTRUMENT=1
export HMT_PT=/home/younes/arma3-marl/pol_1200_g1_instr.pt
L=/mnt/data/instr_g1.log; : > "$L"
{ echo "═══ REJEU INSTRUMENTE, graine 1 — debut $(date +%H:%M:%S) ═══"
  ./.venv/bin/python -u boucle.py 1200
  echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
echo TERMINE >> /mnt/data/instr_journal.txt
