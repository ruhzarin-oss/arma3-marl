#!/usr/bin/env bash
# ETAGE 1 — le vrai champ PUIS le placebo, meme barheme, memes 5 graines.
# Le placebo n est pas optionnel : s il passe aussi, c est la capacite du reseau qui paie.
cd /home/younes/arma3-marl
P=./.venv/bin/python
echo "$(date -Is) DEPART etage 1 — champ de risque, portee 100 m, 5 graines" > /tmp/etage1_coeur.log
$P agent_complet.py --champ > RESULTAT_ETAGE1_CHAMP.log 2>&1
echo "$(date -Is) champ TERMINE (code $?)" >> /tmp/etage1_coeur.log
$P agent_complet.py --champ --placebo > RESULTAT_ETAGE1_PLACEBO.log 2>&1
echo "$(date -Is) placebo TERMINE (code $?)" >> /tmp/etage1_coeur.log
