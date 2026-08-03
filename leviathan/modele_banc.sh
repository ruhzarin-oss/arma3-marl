#!/usr/bin/env bash
# modele_banc.sh — bras A du test de valeur : trois graines, BANC SEUL.
# Criteres : CRITERES_TEST_VALEUR.md (dfe3e85f04161572). Meme architecture, memes
# hyperparametres, MEME nombre de pas de gradient que le bras mixte : seules les donnees different.
#
# Lot de 192 et non 32 : mesure du 31/07, un pas coute le meme temps a 32 et a 192 — le goulot est
# le lancement des noyaux GPU, pas le calcul. Six fois plus de donnees par pas, gratuitement.
# Les trois graines tournent EN MEME TEMPS : le modele fait 2 M de parametres, la carte en a 24 Go.
set -u
LEV=/home/younes/arma3-marl/leviathan
PY=/home/younes/env_isaaclab/bin/python3
cd "$LEV" || exit 2
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
PAS=${PAS:-5000}
for g in 0 1 2; do
  $PY monde_rssm.py --corpus banc --graine $g --pas $PAS --lot 192 --longueur 50 \
      --held-out envelop --sortie "modele_banc_g$g.pt" > "log_modele_banc_g$g.txt" 2>&1 &
done
wait
echo "--- bilan ---"
for g in 0 1 2; do echo "graine $g : $(tail -2 log_modele_banc_g$g.txt | head -1)"; done
echo "BRAS_BANC_DONE"
