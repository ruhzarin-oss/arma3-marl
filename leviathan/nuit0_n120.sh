#!/usr/bin/env bash
# nuit0_n120.sh — porte n de 60 a 120 sur A=8 et A=12. Deux buts en une collecte :
#  (a) AFFUTER les deux cibles retenues de la porte (classements par PRISE) en reduisant le bruit
#      de la cible elle-meme ;
#  (b) SONDER si les classements par PERTES se stabilisent a n=120 dans la metrique Spearman. Le
#      cout est LA variable qui separe dans toute notre recherche : perdre cette famille de
#      verdicts par manque de repetitions serait cher.
# Regle posee AVANT la mesure : si la borne basse Spearman des pertes atteint 0,60 a n=120, un
# addendum v3 AJOUTE la cible a la porte — et cette decision se prend avant toute evaluation d un
# modele, jamais apres. Durcir une porte avant de juger est sain ; la retoucher apres avoir vu la
# copie ne l est jamais.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
VIVANTS=$(pgrep -cf "staging/server([0-9]|1[01])\.cfg" || true)
if [ "${VIVANTS:-0}" -lt 8 ]; then
  echo "REFUS : ${VIVANTS:-0} instances de ferme debout sur 8."
  exit 3
fi
/home/younes/env_isaaclab/bin/python3 nuit0.py --n 120 --ags 8,12 --instances 8
