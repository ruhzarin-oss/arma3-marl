#!/bin/bash
# relancer.sh <port> <cfg> <profiles> <journal> — RELANCER UN BANC SANS SE MENTIR.
#
# ⚠️ POURQUOI CE SCRIPT EXISTE. Ma procedure de relance a menti deux fois :
#   · `pkill -f "port=6002"` a tue MA PROPRE COMMANDE, dont le texte contenait le motif ;
#   · un serveur relance avant que l ancien ait relache le port a echoue sur « createPeer
#     failed », pendant que `pgrep` me donnait l ANCIEN pour vivant. J ai lu la sante d un
#     serveur en croyant lire celle d un autre, et perdu une heure.
#
# Il tue par PID, ATTEND que le port soit reellement libre, lance, et VERIFIE que le nouveau
# processus tient. Il ne rend la main qu apres avoir prouve chacune de ces etapes.
set -u
PORT=$1; CFG=$2; PROF=$3; LOG=$4
MODS="-mod=@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment"

for P in $(pgrep -f "arma3server_x64.*port=$PORT"); do kill $P 2>/dev/null; done
for i in $(seq 1 30); do
  pgrep -f "arma3server_x64.*port=$PORT" >/dev/null || break
  sleep 1
done
for P in $(pgrep -f "arma3server_x64.*port=$PORT"); do kill -9 $P 2>/dev/null; done

# LE PORT, PAS LE PROCESSUS : c est lui qui a fait echouer la derniere relance.
for i in $(seq 1 40); do
  ss -lnu 2>/dev/null | grep -q ":$PORT " || break
  sleep 1
done
if ss -lnu 2>/dev/null | grep -q ":$PORT "; then
  echo "ECHEC : le port $PORT est toujours occupe apres 40 s"; exit 1
fi

[ -f "$LOG" ] && mv "$LOG" "${LOG%.out}_$(date +%H%M%S).out"
cd /mnt/data/harmattan-sandbox/arma3server || exit 1
nohup setsid ./arma3server_x64 -config="$CFG" -profiles="$PROF" -port=$PORT -world=Stratis \
  -autoInit "$MODS" -serverMod=@LAMBS_Danger > "$LOG" 2>&1 < /dev/null &
sleep 45
if grep -q "createPeer failed\|Cannot start host" "$LOG"; then
  echo "ECHEC : le serveur n a pas pu prendre le port $PORT"; exit 1
fi
pgrep -f "arma3server_x64.*port=$PORT" >/dev/null && echo "OK : serveur vivant sur $PORT" \
  || { echo "ECHEC : aucun processus sur $PORT"; exit 1; }
