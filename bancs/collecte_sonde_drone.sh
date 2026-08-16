#!/usr/bin/env bash
# collecte_sonde_drone.sh — collecte N repetitions COMPLETES en RELANCANT le serveur.
#
# ⚠️ POURQUOI CE SUPERVISEUR EXISTE. Mesure du 16/08 : le serveur meurt en service, sans
# erreur et sans message — log coupe net apres ~4,5 min. On ne repare pas la mort, on l
# ENCAISSE : des lots courts, une relance, et un journal cumulatif. Une repetition n est
# retenue QUE si ses TROIS bras ont ete journalises ; une repetition coupee en plein
# milieu est jetee, jamais recollee.
#
# ⚠️ UN LOT = UNE REPETITION. Mesure du 16/08, deux fois de suite : le serveur meurt apres
# la PREMIERE repetition, meme apres correction du demontage de l aeronef. On ne lui en
# demande donc plus qu une. `TERMINE` n est PAS attendu : la mort survient au demontage,
# donc apres la derniere ligne utile mais avant la marque de fin.
#
# Usage : collecte_sonde_drone.sh [cible] [lot]      defauts : 20 reps, 1 par lot
set -uo pipefail
CIBLE=${1:-20}
LOT=${2:-1}
SB=/mnt/data/harmattan-sandbox
LOG=$SB/logs/sonde_drone.out
CUM=$SB/logs/sonde_drone_cumul.out

: > "$CUM"
fait=0; run=0
echo "=== collecte : cible $CIBLE reps, $LOT par lot ==="
while [ "$fait" -lt "$CIBLE" ] && [ "$run" -lt 40 ]; do
  run=$((run + 1))
  /home/younes/arma3-marl/bancs/lancer_sonde_drone.sh "$LOT" > /dev/null 2>&1
  sleep 25                                  # le serveur doit exister avant qu on guette sa mort
  # on attend TERMINE, ou la mort du serveur, ou le plafond de temps
  for i in $(seq 1 60); do
    grep -aq "HMT|DR|TERMINE" "$LOG" && break
    pgrep -f "staging/serverDR\.cfg" > /dev/null || { sleep 5; break; }
    sleep 10
  done
  garde=0
  for r in $(seq 1 "$LOT"); do
    # une repetition ne compte QUE si ses 3 bras sont la
    # ⚠️ PAS de `|| echo 0` : `grep -c` ecrit deja 0 et sort en erreur, donc le `||`
    # ajoutait un SECOND zero et le test entier explosait (mesure du 16/08, 2 lots perdus).
    n=$(grep -ac "HMT|DR|rep|$r|" "$LOG" 2>/dev/null)
    n=${n:-0}
    if [ "$n" -ge 3 ] && [ "$fait" -lt "$CIBLE" ]; then
      fait=$((fait + 1)); garde=$((garde + 1))
      grep -a "HMT|DR|rep|$r|" "$LOG" | sed "s/|rep|$r|/|rep|$fait|/" >> "$CUM"
    fi
  done
  echo "lot $run : +$garde retenues -> $fait/$CIBLE"
  pkill -9 -f "staging/serverDR\.cfg" 2>/dev/null; sleep 3
done
echo "=== collecte terminee : $fait reps dans $CUM ==="
