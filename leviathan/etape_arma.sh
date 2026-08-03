#!/usr/bin/env bash
# etape_arma.sh — UNE etape Arma : serveur neuf, chien de garde, pont ferme quoi qu'il arrive.
#
# Principe non negociable de la nuit : chaque etape redemarre le serveur avant elle.
# Ainsi une etape morte ne tue que SA mesure ; la suivante repart saine.
#
#   usage : etape_arma.sh <secondes_max> <script.py> [args...]
set -u
MAX="${1:?usage: etape_arma.sh <secondes_max> <script.py> [args...]}"; shift
BANC="${1:?script}"; shift
LEV=/home/younes/arma3-marl/leviathan
LOG=/tmp/nuit_$(basename "$BANC" .py).log

echo "--- serveur neuf pour $(basename "$BANC")"
bash "$LEV/relancer_meltemi.sh" >/dev/null 2>&1
for i in $(seq 1 40); do
  ss -tlnp 2>/dev/null | grep -q 5826 && break
  sleep 5
done
sleep 10
if ! pgrep -f 'arma3server_x64' >/dev/null; then
  echo "!! serveur non reparti — etape SAUTEE"
  return 2 2>/dev/null || exit 2
fi

echo "--- mesure (chien de garde ${MAX}s) : $(basename "$BANC") $*"
cd "$LEV" || exit 2
timeout -k 20 "$MAX" python3 "$BANC" "$@" > "$LOG" 2>&1
CODE=$?
if [ "$CODE" -eq 124 ]; then
  echo "!! CHIEN DE GARDE : ${MAX}s depassees, etape tuee"
fi
echo "--- code $CODE -> $LOG"
tail -30 "$LOG"
exit "$CODE"
