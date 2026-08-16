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

  # ── 1. la sonde a-t-elle seulement DEMARRE ? ──
  # ⚠️ On ne guette plus la seule presence du process. Mesure du 16/08 : 5 lots sur 6
  # rendaient zero en ~80 s — le serveur ne demarrait pas (port pas encore libere apres
  # le pkill). Un lot qui ne demarre pas doit se DIRE, pas se compter en silence.
  # 300 s : mesure du 16/08, 2 lots perdus parce que le serveur bootait ENCORE a 120 s
  # (CBA + RHS + LAMBS + PinnedDown, c est lourd a charger)
  demarre=0
  for i in $(seq 1 60); do
    grep -aq "HMT|DR|debut" "$LOG" && { demarre=1; break; }
    sleep 5
  done
  if [ "$demarre" -eq 0 ]; then
    echo "lot $run : LA SONDE N A PAS DEMARRE en 300 s -- $(tail -1 "$LOG" 2>/dev/null | cut -c1-90)"
    pkill -9 -f "staging/serverDR\.cfg" 2>/dev/null; sleep 12
    continue
  fi

  # ── 2. on attend les 3 bras, la mort du serveur, ou le plafond ──
  for i in $(seq 1 60); do
    [ "$(grep -ac "HMT|DR|rep|" "$LOG" 2>/dev/null)" -ge $((LOT * 3)) ] && break
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
    # ⚠️ UNE REPETITION SANS AZIMUT EST UN VOID, PAS UNE PERTE. Les criteres deposes la
    # comptent (plafond : 4 VOID sur 20). La jeter en silence serait choisir ses donnees
    # apres coup. Elle tient en UNE ligne `bras|AUCUN`, et elle est retenue comme telle.
    if grep -aq "HMT|DR|rep|$r|bras|AUCUN" "$LOG" 2>/dev/null; then n=3; fi
    if [ "$n" -ge 3 ] && [ "$fait" -lt "$CIBLE" ]; then
      fait=$((fait + 1)); garde=$((garde + 1))
      grep -a "HMT|DR|rep|$r|" "$LOG" | sed "s/|rep|$r|/|rep|$fait|/" >> "$CUM"
    fi
  done
  if [ "$garde" -eq 0 ]; then
    echo "lot $run : DEMARRE mais repetition INCOMPLETE ($(grep -ac 'HMT|DR|rep|' "$LOG" 2>/dev/null) lignes sur $((LOT * 3)))"
  else
    echo "lot $run : +$garde retenue -> $fait/$CIBLE"
  fi
  # 12 s et pas 3 : le port doit etre rendu avant la relance, sinon le serveur suivant
  # ne demarre pas du tout (5 lots perdus le 16/08)
  pkill -9 -f "staging/serverDR\.cfg" 2>/dev/null; sleep 12
done
echo "=== collecte terminee : $fait reps dans $CUM ==="
