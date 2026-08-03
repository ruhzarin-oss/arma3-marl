#!/usr/bin/env bash
# nuit0_n60.sh — porte n de 20 a 60 sur les rapports de force A=8 et A=12.
# Ce n est PAS une nouvelle mesure : c est la MEME, avec assez de repetitions pour que le
# classement des manoeuvres soit stable. Mesure du 31/07 : a n=20, les classements ne sont stables
# que dans 24 a 48 pct des reechantillonnages, tres loin des 80 pct exiges — l ecart-type des
# pertes (0,87) depasse les ecarts entre manoeuvres (0,2 a 0,5). On mesurait du bruit.
# A=4 est ECARTE : a 0-10 pct de prise, aucun classement n y est separable a un cout raisonnable.
# La collecte est idempotente (elle saute ce qui existe), donc elle n ajoute que le manquant.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
VIVANTS=$(pgrep -cf "staging/server([0-9]|1[01])\.cfg" || true)
if [ "${VIVANTS:-0}" -lt 12 ]; then
  echo "REFUS : ${VIVANTS:-0} instances de ferme debout sur 12."
  exit 3
fi
/home/younes/env_isaaclab/bin/python3 nuit0.py --n 60 --ags 8,12 --instances 12
