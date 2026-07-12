#!/bin/bash
# Programme de la nuit HARMATTAN — tourne DETACHE sur la workstation, survit a la fermeture du Mac.
# Enchaine des scenarios de combat de la prise vivante, serveur frais + timeout par run, ecrit le rapport du matin.
ND=/mnt/data/harmattan-sandbox/logs/night
mkdir -p "$ND"
PY=/home/younes/arma3-marl/.venv/bin/python
cd /home/younes/arma3-marl
REP="$ND/MORNING_REPORT.txt"
LOG="$ND/night.log"
echo "================ PROGRAMME DE LA NUIT — $(date) ================" > "$REP"
echo "Prise vivante (avatar branche temps reel sur Arma) en COMBAT, terrain degage sud-Paros." >> "$REP"
echo "Chaque run : serveur frais, OPFOR a decouvert IA active, cerveau distille + intention de commande." >> "$REP"
echo "" >> "$REP"
echo "NUIT DEBUT $(date)" > "$LOG"

run() {  # label server dist n_en skill seed cycles
  local label=$1 srv=$2 dist=$3 nen=$4 skill=$5 seed=$6 cyc=$7
  echo "--- $label (server$srv dist=$dist n_en=$nen skill=$skill) $(date +%H:%M:%S) ---" | tee -a "$LOG"
  timeout 280 "$PY" avatar_fight.py "$srv" "$dist" "$nen" "$skill" "$seed" "$cyc" "$label" > "$ND/$label.log" 2>&1
  local rc=$?
  local summary=$(grep ">>>" "$ND/$label.log" | tail -1)
  if [ -z "$summary" ]; then summary=">>> $label | PAS DE RESULTAT (rc=$rc, voir $label.log)"; fi
  echo "$summary" | tee -a "$LOG" >> "$REP"
  echo "" >> "$REP"
  sleep 4
}

# ---- Bloc A : ouvrir la fusillade + micro-combats (serveurs 6..14) ----
echo "## BLOC A — fusillade & micro-combats" >> "$REP"
run A1_base    6 70 3 0.50 41 300
run A1_proche  7 45 2 0.40 42 300
run A1_dur     8 90 3 0.60 43 300
run A3_1v1     9 45 1 0.50 44 300
run A3_1v2    10 45 2 0.50 45 300
run A1_rep    11 60 3 0.50 46 300
run A3_1v1b   12 50 1 0.55 47 300
run A1_tres_proche 13 30 2 0.50 48 300

# ---- Synthese ----
echo "## SYNTHESE" >> "$REP"
echo "Runs ou l'avatar a PRIS LE FEU (feu_recu=True) :" >> "$REP"
grep ">>>" "$REP" | grep -c "feu_recu=True" >> "$REP"
echo "Runs avec REACTION (1re_reaction != None) :" >> "$REP"
grep ">>>" "$REP" | grep -cE "1re_reaction=(COUVERT|SUPPRESSER)" >> "$REP"
echo "Issues :" >> "$REP"
grep ">>>" "$REP" | grep -oE "issue=[A-Z _]+" | sort | uniq -c >> "$REP"
echo "" >> "$REP"
echo "PROCHAINES MARCHES (a faire en interactif, pas tournees cette nuit) :" >> "$REP"
echo " - B5 latence socket direct (~8-10 Hz)  - B6 couplage corps H1 (dehors physique)  - mettre la memoire a jour" >> "$REP"
echo "NUIT FINIE $(date)" | tee -a "$LOG" >> "$REP"
echo "NIGHT_DONE"
