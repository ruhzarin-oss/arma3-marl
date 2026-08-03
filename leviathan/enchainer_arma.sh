#!/usr/bin/env bash
# enchainer_arma.sh — la suite de la chaine Arma, apres A1/A2. Sequentiel, un seul serveur.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
while pgrep -f 'nuit_arma_1.sh' >/dev/null; do sleep 30; done
sleep 5
bash nuit_arma_2.sh
bash a5_rejeux.sh 2>&1 | tee -a /tmp/nuit_journal.txt
echo "CHAINE_ARMA_COMPLETE" | tee -a /tmp/nuit_journal.txt
