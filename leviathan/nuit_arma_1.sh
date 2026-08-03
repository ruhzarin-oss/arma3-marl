#!/usr/bin/env bash
# nuit_arma_1.sh — A1 (tete de chaine) puis A2 (courbe n2, DEUX essais maximum).
# Resultats ecrits en continu. Une etape morte ne tue que sa mesure.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
J=/tmp/nuit_journal.txt
echo "===== NUIT ARMA — debut $(date '+%H:%M') =====" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### A1 — TETE DE CHAINE #####" | tee -a "$J"
bash etape_arma.sh 900 a1_tete.py 2>&1 | tee -a "$J"
A1=${PIPESTATUS[0]}
if [ "$A1" -ne 0 ]; then
  echo "!! A1 ECHOUE (code $A1) : la chaine Arma S'ARRETE et le dit." | tee -a "$J"
  echo "A1_ECHEC" >> "$J"
  exit 2
fi

echo "" | tee -a "$J"
echo "##### A2 — COURBE N2, ESSAI 1 : 12 tireurs, timeout 45 s #####" | tee -a "$J"
bash etape_arma.sh 1500 mesurer_suppression.py --theatre altis --reps 6 --duree 40 \
     --paires 2 --dist 100 --dsup 120 --out courbe_suppression_12.json 2>&1 | tee -a "$J"
E1=${PIPESTATUS[0]}
echo "A2 essai 1 : code $E1" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### A2 — ESSAI 2 : VARIANT DIAGNOSTIQUE, 4 tireurs au lieu de 12 #####" | tee -a "$J"
echo "  Ce n'est pas une repetition. Si 4 passe et 12 meurt meme a 45 s," | tee -a "$J"
echo "  l'hypothese « charge » est confirmee par construction." | tee -a "$J"
bash etape_arma.sh 1500 mesurer_suppression.py --theatre altis --reps 6 --duree 40 \
     --paires 1 --dist 100 --dsup 120 --out courbe_suppression_04.json 2>&1 | tee -a "$J"
E2=${PIPESTATUS[0]}
echo "A2 essai 2 : code $E2" | tee -a "$J"

echo "" | tee -a "$J"
echo "===== NUIT ARMA 1 terminee $(date '+%H:%M') =====" | tee -a "$J"
echo "NUIT_ARMA_1_DONE" | tee -a "$J"
