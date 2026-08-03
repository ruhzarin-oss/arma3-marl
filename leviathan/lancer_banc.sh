#!/usr/bin/env bash
# lancer_banc.sh — LA façon de lancer un banc de mesure. Pas d'autre.
#
# Pourquoi : le pont d'Arma ne parle qu'à UN client, et l'extension ne libère JAMAIS la
# place d'un client disparu. Fermer proprement à la sortie ne suffit pas (un processus
# tué n'exécute plus rien), et un gestionnaire de signal ne suffit pas non plus (mesuré
# le 27/07). Résultat : après tout arrêt brutal, le pont est muet jusqu'au redémarrage.
#
# Donc on arrête de réparer la fermeture, et on garantit le DÉPART : serveur neuf avant
# chaque banc. Soixante secondes, et toute une classe de pannes disparaît.
#
#   usage : lancer_banc.sh <script.py> [arguments...]
set -u
BANC="${1:?usage: lancer_banc.sh <script.py> [args...]}"; shift
LEV=/home/younes/arma3-marl/leviathan
LOG=/tmp/banc_$(basename "$BANC" .py).log

echo "[1/4] serveur neuf"
bash "$LEV/relancer_meltemi.sh" >/dev/null 2>&1
for i in $(seq 1 30); do
  ss -tlnp 2>/dev/null | grep -q 5826 && break
  sleep 5
done
sleep 8
pgrep -f 'arma3server_x64' >/dev/null || { echo "  !! le serveur n'est pas reparti"; exit 2; }

echo "[2/4] le pont repond ?"
if ! timeout 45 python3 "$LEV/etat.py" >/tmp/banc_etat.out 2>&1; then
  echo "  !! pont muet au demarrage — on n'engage pas la mesure"; cat /tmp/banc_etat.out; exit 2
fi
sed 's/^/  /' /tmp/banc_etat.out

echo "[3/4] mesure : $(basename "$BANC") $*"
rm -f /tmp/hmt_stop
cd "$LEV" || exit 2
python3 "$BANC" "$@" > "$LOG" 2>&1
CODE=$?

echo "[4/4] termine (code $CODE) -> $LOG"
tail -25 "$LOG"
