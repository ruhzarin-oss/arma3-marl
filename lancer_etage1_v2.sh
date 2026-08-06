#!/usr/bin/env bash
# ETAGE 1, dans le monde QUI TUE. Trois bras CONTEMPORAINS — meme code, meme soiree.
# La regle nee de la reference fantome : un chiffre d hier est un autre monde.
cd /home/younes/arma3-marl
P=./.venv/bin/python
echo "$(date -Is) DEPART etage 1 v2 — monde letal, 3 bras, 5 graines" > /tmp/etage1v2_coeur.log
$P agent_complet.py --champ            > RESULTAT_V2_CHAMP.log    2>&1
echo "$(date -Is) champ fini ($?)"    >> /tmp/etage1v2_coeur.log
$P agent_complet.py --champ --placebo  > RESULTAT_V2_PLACEBO.log  2>&1
echo "$(date -Is) placebo fini ($?)"  >> /tmp/etage1v2_coeur.log
$P agent_complet.py                    > RESULTAT_V2_SANSCHAMP.log 2>&1
echo "$(date -Is) sans-champ fini ($?)" >> /tmp/etage1v2_coeur.log
