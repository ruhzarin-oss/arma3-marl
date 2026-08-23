#!/bin/bash
# LE TEMOIN (regle 16) : le MEME protocole a 10 actions, aujourd hui, sur ce code.
# Sans lui, un 0 % a 13 actions peut aussi bien accuser ma modification de `NA` que les
# postures. Meme remarque que ci-dessus : on appelle le FICHIER, pour que la porte tourne.
cd /home/younes/arma3-marl || exit 1
L=/mnt/data/temoin10.log
: > "$L"
export HMT_NA=10
export HMT_PT=/home/younes/arma3-marl/boucle_pol_10actions_rejoue.pt
{
echo "═══ TEMOIN 10 ACTIONS — debut $(date +%H:%M:%S) ═══"
./.venv/bin/python -u boucle.py 140
echo "═══ fin $(date +%H:%M:%S) ═══"
} >> "$L" 2>&1
